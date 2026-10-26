# 02 — Topic & Question (Question Bank)

> Parent: [`00-master-overview.md`](00-master-overview.md)
> Scope: `topic`, `question`, API `/api/v1/topic` + `/api/v1/question`, the three-column editor with autosave.

---

## 1. Entity & Tables

### 1.1 `topic`

| Column | Type | Notes |
|-------|------|-------|
| `name` | VARCHAR(140) PK | slug of `title` (00 §5) |
| `title` | VARCHAR(255) NOT NULL | |
| `category` | VARCHAR(20) NOT NULL | `cub`/`scout`/`rover`; index `(category)` |
| `idx` | INTEGER NOT NULL default 0 | order within the category; index `(category, idx)` |
| `creator_id` | INTEGER → `ab_user.id` SET NULL | |
| `created_at`, `updated_at` | DATETIME default now | |

**No soft delete** — `DELETE` = hard remove (child questions lose `topic_id` → NULL; questions are **not** deleted).

### 1.2 `question`

| Column | Type | Notes |
|-------|------|-------|
| `name` | VARCHAR(140) PK | slug of `questionCode` (00 §5) |
| `questionCode` | VARCHAR(40) NOT NULL default `'Mini Challenge'` | display title |
| `question` | TEXT NOT NULL | **HTML** prompt from the TextEditor |
| `description` | TEXT nullable | optional **HTML** context shown before the prompt |
| `questionType` | VARCHAR(20) NOT NULL default `'Multiple Choice'` | `Multiple Choice` / `Essay` |
| `optionA`…`optionD` | TEXT nullable | MC options (HTML) |
| `referenceAnswer` | TEXT nullable | Essay reference answer |
| `correctAnswer` | VARCHAR(8) nullable | `a`/`b`/`c`/`d` (lowercase) |
| `category` | VARCHAR(20) NOT NULL | index `(category)`, `(category,status)`, `(category,difficultyLevel)` |
| `difficultyLevel` | VARCHAR(20) NOT NULL default `'Easy'` | **the DB/API typo is carried over** (legacy `tingak_kesulitan`) |
| `status` | VARCHAR(20) NOT NULL default `'Active'` | `Active`/`Inactive` |
| `creator_id` | INTEGER → `ab_user.id` SET NULL | |
| `topic_id` | VARCHAR(140) → `topic.name` SET NULL | index `(topic_id)` |
| `disabled` | BOOLEAN NOT NULL default 0 | soft delete; index |
| `disabled_at` | DATETIME nullable | |
| `created_at`, `updated_at` | DATETIME default now | |

Fixed enums (DTO constants): `CATEGORY`, `DIFFICULTY_LEVEL = (Easy, Medium, Hard)`, `QUESTION_TYPE`, `OPTION_LETTERS = (a,b,c,d)`, `STATUS = (Active, Inactive)`.

---

## 2. Flow: Topic (`/api/v1/topic`)

All endpoints: 401 when not logged in. The `_author_or_mod()` gate is called on mutations but **always returns None** (it never rejects — hazard 00 §6.3).

### 2.1 `GET /` (list)

`limit` default **200** (clamp 1..500), `offset ≥0` (bad → 400 `limit_or_offset_invalid`). Filter `?category=` (exact match, no enum validation). Order `category, idx, name`. → **200** `{ items: [TopicOut…] }` (**no `total`**).

### 2.2 `GET /<name>` → 404 `topic_not_found` / **200** object.

### 2.3 `POST /` — rate 30/minute

1. `TopicCreate`: `title` 1..255 required; `category` must be in the enum else `category_category_must_be_cub_scout_or_rover`; `idx` int ≥0 default 0; `creatorId` optional int.
2. Service: empty `title.strip()` → 409 `title_required`.
3. `name = _next_name(title)`: slug; if taken → try `slug-0001`…`slug-0999`; exhausted → 409 `could_not_generate_unique_name`.
4. Insert + **service commit** → audit `topic_created` `details={"category"}` → API commit → **201** `TopicOut`.
5. ⚠ `creatorId` from the client is **trusted** (`dto.creator_id or current_user.id`).

### 2.4 `PATCH /<name>` — rate 30/minute

`TopicUpdate` (`extra="ignore"`, all optional, empty model validator → `value_no_fields_to_update` → 400). Service: missing → 404 `topic_not_found`; `title` re-stripped when a string; `setattr` per key → commit → audit `topic_updated` `details.changed` → **200**.

### 2.5 `DELETE /<name>` — rate 10/minute

Missing → 404. **Hard delete** + commit → audit `topic_deleted` → **204**.

### 2.6 `POST /reorder` — rate 30/minute

Raw body validation (not Pydantic):
- `items` not a list → 400 `items_must_be_list`
- element not a dict → 400 `items_malformed`
- `name` not a non-empty string → 400 `item_name_required`
- `idx` not an int or <0 → 400 `item_idx_invalid` (⚠ `bool` passes `isinstance`)

Service: per item `get_by_name` — **unknown names are silently skipped**; set `row.idx`; one commit. Audit `topic_reordered` `details={"count"}` → **200** `{ count: N }`.

### 2.7 `TopicOut` shape

`{ name, title, category, idx, creatorId, createdAt, updatedAt }` (camelCase, timestamp +00:00).

---

## 3. Flow: Question (`/api/v1/question`)

### 3.1 `GET /` (list)

`limit` default 100 (1..200), `offset ≥0` → 400 `limit_or_offset_invalid`.
Filters: `category`, `status`, **`difficultyLevel` OR `difficulty_level`** (the typo spelling is the official param name — legacy), `topic`/`topicId` → `topic_id ==`, `q` (ilike `question OR questionCode`), `includeDisabled`/`include_disabled` (truthy: `1,true,yes,on`).
Default **hides `disabled=true`**. Order `created_at DESC`.
→ **200** `{ items, total }` — ⚠ `total` is computed with only `category`+`status`+flag (it **ignores `difficultyLevel`/`topic`/`q`**) → inaccurate pagination (hazard 00 §14.7).

### 3.2 `GET /option-list` → **200**

```json
{"category":["cub","scout","rover"],"difficultyLevel":["Easy","Medium","Hard"],
 "questionType":["Multiple Choice","Essay"],"option":["a","b","c","d"],"status":["Active","Inactive"]}
```

### 3.3 `GET /<name>` → 404 `question_not_found` / **200** `QuestionOut` (including `disabled` rows — detail is not filtered).

### 3.4 `POST /` — rate 30/minute

1. Gate login (+ `_author_or_mod` no-op).
2. `QuestionCreate` — defaults: `questionCode="Mini Challenge"`, `questionType="Multiple Choice"`, `difficultyLevel="Easy"`, `status="Active"`; optional `creatorId`, `topicId ≤140`.
   - Field validators: type → `question_type_must_be_multiple_choice_or_essay`; category → `category_category_must_be_cub_scout_or_rover`; difficulty → `difficulty_level_invalid`; status → `status_invalid`; `correctAnswer` must be a–d (case-insensitive, output lowercase; `""`→`None`) else `correct_answer_must_be_a_b_c_or_d`.
   - **Model validator `_check_business`** (when `questionType == "Multiple Choice"`): options A–D non-empty (check order A→D) else `value_pg_requires_option_a|_b|_c|_d`; `correctAnswer` required else `value_pg_requires_correct_answer`. **When Essay**: a reference `answer` is required else `value_essay_requires_reference_answer`.
3. Service: resolve key aliases (`questionCode|question_code`, …); `name = _next_name(questionCode)` → `slug` / `slug-{year}-0001`…`-0999` → exhausted: 409 `could_not_generate_unique_name`; insert + service commit.
4. Audit `question_created` `details={"category","type"}` → commit → **201** `QuestionOut`.

### 3.5 `PATCH /<name>` — rate 30/minute

`QuestionUpdate` = all optional + `value_no_fields_to_update` + the same field validators **only when a value is sent** — ⚠ **no `_check_business`** → a MC↔Essay transition is not re-validated (hazard 00 §14.6). Full alias map to snake_case → `setattr` → commit → audit `question_updated` → **200**. Missing → 404 `question_not_found`.

### 3.6 `DELETE /<name>` — rate 10/minute (**soft**)

Missing → 404. `disabled=True`, `disabled_at=datetime.utcnow()` (naive) → commit → audit `question_soft_deleted` → **204**.

### 3.7 `POST /<name>/restore` — rate 10/minute

`disabled=False`, `disabled_at=None` → audit `question_restored` → **200** `{message:"restored"}`; 404 when missing.

### 3.8 `DELETE /<name>/purge` — rate 5/minute (**hard**)

`session.delete` → audit `question_purged` → **204**; 404 when missing. The docstring says "admin-only" but **no role check** is performed.

### 3.9 `QuestionOut` shape

`{ name, questionCode, question, description, questionType, optionA…D, referenceAnswer, correctAnswer, category, difficultyLevel, status, creatorId, topicId, disabled, disabledAt, createdAt, updatedAt }`. Null fields (including `description`) are omitted from the wire. List rows drop `description` (owners pay ~6 MB for 200 rows otherwise); `GET /<name>` returns it.

---

## 4. List Contract & Query Conventions

| Aspect | Rule |
|---|---|
| Question list ordering | `created_at DESC` |
| Topic list ordering | `category, idx, name` |
| `q` search | `ilike %q%` over `question OR description OR questionCode` (topic: no `q`) |
| Soft-delete view | excluded from default lists; `?includeDisabled=true` includes them; detail/restore still access disabled rows |
| `count_by_category` | the service exists but no API uses it (dead) |

---

## 5. Question Editor (frontend — autosave logic)

Component `components/Question/QuestionEditor.vue`, used by the `/question-editor` page.

1. **Dirty tracking**: `watch(form, deep)` → `isDirty = JSON.stringify(form) !== snapshot`; the snapshot is the form state at load or at the last **successfully sent** payload.
2. **Local validation** (same as the form): `hasRichContent(html)` = has an `<img>` or has text after stripping tags, `&nbsp;`/`&#160;`/`&#xa0;`, and whitespace; messages `Pertanyaan wajib diisi` → "The question is required", `Opsi A/B/C/D wajib diisi` → "Option A/B/C/D is required", `Pilih jawaban yang benar` → "Select the correct answer", `Jawaban referensi wajib diisi` → "The reference answer is required".
3. **Autosave**: debounce **3000 ms** → `runAutoSave()`:
   - skip when the snapshot is unchanged, when a request is already in flight, or when validation fails (sets `touched`);
   - payload built once per request; for **Essay** `optionA/B/C/D` + `correctAnswer` are omitted; empty rich HTML description is sent as `null`;
   - `PATCH /question/{name}` → success: snapshot = the **submitted** form state (edits typed during the request stay dirty and re-schedule); failure: `failed` state + toast, no automatic retry;
   - switching `questionName` flushes dirty draft edits to the previous question, cancels the timer, invalidates the in-flight response, and resets the form; leaving the editor flushes pending valid edits (unless a request is in flight).
4. **Status badge**: `saving` → orange "Saving…"; `saved` → green "Saved {relative}" (`just now` <5s / `Ns ago` / `Nm ago`); `failed` → red "Failed to save".
5. **Save**/**Cancel** disabled when clean or saving; **Save** toasts success only when the request succeeded; Cancel → reload + emit `discard`.
6. MC answer selection: radio `name="jawaban-benar-editor"` → `name="correct-answer-editor"`; the selected row is highlighted green; empty options are shown as `(kosong)` → `(empty)` in italics.

---

## 6. Error Catalog (this domain)

| Code | message |
|------|---------|
| 400 | `title_required`*, `category_category_must_be_cub_scout_or_rover`, `value_no_fields_to_update`, `items_must_be_list`, `items_malformed`, `item_name_required`, `item_idx_invalid`, `limit_or_offset_invalid` |
| 400 | `question_required`, `questionType_question_type_must_be_multiple_choice_or_essay` (the alias follows the sent key), `category_category_must_be_…`, `difficultyLevel_difficulty_level_invalid`, `status_status_invalid`, `correctAnswer_correct_answer_must_be_a_b_c_or_d`, `value_pg_requires_option_a/_b/_c/_d`, `value_pg_requires_correct_answer`, `value_essay_requires_reference_answer`, `questionCode_too_long`, `topicId_too_long` |
| 401 | `unauthorized` |
| 404 | `topic_not_found`, `question_not_found` |
| 409 | `title_required`†, `could_not_generate_unique_name` |
| 429 | `rate_limit_exceeded` |

\* Missing `TopicCreate` field (Pydantic) → `title_required`. † `TopicService.create` (empty after strip) also → 409 `title_required`.

---

## 7. UI Flow (Vue)

### 7.1 Question list — `/question` (`question`)

- Header: **Open Editor** → `question-editor`; **Add Question** → `question-new` with `?type=mc` (always MC; `type=essay` only via manual URL). Subtitle `{{total}} questions` (from the server `total`).
- Filters: search (client-side: `questionCode` or tag-stripped `question`) + category/difficulty/status (**server-side**, watch → reload debounce 200 ms).
- Columns: Code · Type (`Essay` blue / MC gray badge) · Category (blue badge) · Difficulty · Status (`Active` green / else gray badge) · Actions.
- Row = router-link to `question-detail`; row actions `@click.stop`.
- Delete: `dialog.danger` "Delete Question" → `DELETE` → remove the row + `total--` + toast. On error → toast.
- Empty → `<EmptyStateLayout name="Question" />`.

### 7.2 Question form — `/question/new`, `/question/:name/edit`

- Sticky header: breadcrumb; an orange **"Unsaved"** badge when `isDirty`; **Cancel** → list; **Save** (`:loading`).
- `isEssay = route.query.type === 'essay'` (only affects the create form).
- Load `listUsers()` for the Creator autocomplete (failure → non-fatal); edit → `GET /question/{name}` (failure → `submitError`).
- S1 Detail: Question Code default `'Mini Challenge'`; **Type disabled on edit**.
- S2 Content: optional `TextEditor` for the description, then `TextEditor` for the question (upload → `POST /files/upload`); when MC → 4 option TextEditors with a compact toolbar (bold, italic, link, image) + a correct-answer radio (selected row border/bg green); when Essay → 1 editor "Answer (reference)".
- S3 Settings: Category, Difficulty, Status, Creator (Autocomplete, default the current account).
- Submit validation (JS, set `touched`, abort when there are errors): question required; MC: A–D required + `correctAnswer` selected; Essay: `answer` required. Description is optional; empty rich HTML is sent as `null`. A question/option counts as content when it has text **or** an `<img>`; tag-only HTML (`<p></p>`) is empty.
- Payload: `{questionCode, questionType, question, description, category, difficultyLevel, status, creatorId?}` + (MC: `optionA…D, correctAnswer`) / (Essay: `referenceAnswer`). Edit → PATCH → `/question/{name}`; create → POST → `/question/{created.name}`; failure → Alert `submitError` (no toast).

### 7.3 Question detail — `/question/:name`

Category/type/difficulty/status badges; when present, description in muted text above a divider; question (fallback `(empty)`); list of options a–d `pgOptions` rendered as rich HTML (image-only options supported, images capped at 192px via `max-h-48`, tag-only HTML shows `(empty)`) — the row where `letter === correctAnswer` gets a green border + green circle + a "Correct" label; Essay → reference answer; dl Info (Category, Difficulty, Status, Type). Actions: **Edit**, **Question Bank**. All rich HTML on this page passes through `sanitizeHtml` (DOMPurify allowlist: question tags, safe URI schemes incl. `data:image`, CSS properties whitelist).

### 7.4 Three-column editor — `/question-editor`

- Grid `300px | 1fr | 320px`. Left: `QuestionOutline`; Center: `QuestionEditor` (or the empty state "Pilih soal di sebelah kiri…" → "Select a question on the left…"); Right: a read-only "Settings" panel (topic title from `topicId`, Category, Type, Difficulty, Status, character count of question + description).
- `QuestionEditor` uses the same rich text form as §7.2: description + question editors (full toolbar) and, for MC, four option editors with the compact toolbar (bold, italic, link, image).
- **Selection via URL**: `?question={name}` → `router.replace` → `GET /question/{name}`; save → toast "Question saved"; discard → reload.
- Header: Back → `home`; title `Question Bank — {questionCode}`; **Question List** → `question`.

### 7.5 Outline — `QuestionOutline` (+ `TopicRow`)

- Load `Promise.all([listTopics, listQuestions({limit:500})])`; failure → toast.
- Grouping: categories ordered `cub→scout→rover` (empty groups are discarded); topics within a group ordered by `idx`; questions grouped by `topicId ?? '__none__'`.
- Per group: a ghost **"Add {Category} Topic"** button (`idx` defaults to the group's topic count). Empty state "Belum ada topik" → "No topics yet" + a button.
- `TopicRow`: expandable (default open), counts `{n} questions`, hover actions edit/delete topic (when `allowEdit`), question items with a `help-circle` icon for MC / `file-text` for Essay + an `MC`/`Essay` badge, title = `questionCode` → text stripped to 80 chars → `(tanpa judul)` → `(untitled)`, the active row is highlighted.
- **Delete topic**: `dialog.danger` — *"Deleting a topic will detach the questions inside it (the questions are not deleted). Continue?"* → `DELETE /topic/{name}` → toast + reload.
- **Delete question**: *"Deleted questions cannot be restored. Continue?"* → `DELETE /question/{name}` → toast + reload.
- Drag-reorder: a no-op handler ("Reorder UI belum diaktifkan" → "The reorder UI is not enabled yet"); `reorderTopik` → `reorderTopic` is never called (dead).

### 7.6 Topic modal — `TopicModal`

Fields: Title (required, `keyup.enter` submits), Category select, Order (`idx` number). Validation: empty `judul.trim()` → `title.trim()` → toast error. Create → `POST` + toast "Topic created"; edit → `PATCH` + "Topic updated"; `emit('saved')` + close.

### 7.7 Question modal — `QuestionModal`

The full form as in §7.2 (type disabled on edit) + always sends `topicId`. Identical validation. Toast "Question created/updated" + `emit('saved')`.

### 7.8 Page access

All question/topic routes have `meta.role:'admin'` (declarative, **not enforced by the guard**) — the sidebar only shows them to staff; a student can access them via a direct URL and the backend does not reject either (hazard 00 §6.3).
