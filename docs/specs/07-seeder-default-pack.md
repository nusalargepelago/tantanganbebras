# 07 — Default Seeder Pack

> Parent: [`00-master-overview.md`](00-master-overview.md)
> Location: `backend/scripts/seed_default.py` (extends `backend/scripts/seed_demo.py`)
> Loader: `python -m scripts.seed_default` (CLI, no ZIP/CSV — data is embedded as Python tuples)
>
> **Identifier note:** the current Python script still uses the legacy Indonesian identifiers (`siswa`, `soal`, `siswaId`, …). This spec records the **English target contract** for the port; the mapping is the one in [00 §11](00-master-overview.md#11-enum-catalog-reference) and the glossary below. Sample **data** content (topic slugs, question text, school names) is kept verbatim — it is data in the database, not an identifier.

---

## 1. Purpose

- Fresh install: after `flask db upgrade`, one command produces an **exercisable** demo install — every feature has data (question bank, events, practices, attempts, autosaves, todos).
- A data reference for re-implementation: the question content (36 items), the naming scheme, and the determinism rules are recorded here.
- Not a production replacement: sample data only; static passwords.

## 2. Business Scenario

Three students, one per category — two of them have different activity trails so the UI shows every state (Completed / In Progress / not started):

| Account | Category | Profile | Trail |
|---|---|---|---|
| admin / moderator / creator / evaluator | — | staff | login via `POST /api/v1/auth/login` |
| budi | cub | SMP Negeri 1 Bandung | event attempt **completed** (score 70) + practice **completed** (score 70) |
| siti | scout | SMP Negeri 2 Yogyakarta | event attempt **in progress** + practice **in progress** (3 autosaves) |
| rani | rover | SMA Negeri 1 Surabaya | active student, no attempts yet |

## 3. How to Run

```bash
cd backend
$env:SECRET_KEY = "x" * 40          # Windows PowerShell
.venv/Scripts/python.exe -m scripts.seed_default
```

- `SECRET_KEY` / `DATABASE_URL` are defaulted inside the script (mimicking `seed_demo.py`: `instance/app.db`, not `app.db` — `run.py` does not auto-load `.env`).
- Order: `seed_demo.main()` (accounts + roles, idempotent) → domain seeds in a fresh `app_context` → a single `commit`.
- Safe to run repeatedly (§5).

## 4. Inventory (Data Contents)

| Table | Count | Names / contents |
|---|---|---|
| `ab_role` | +1 | `Batch Evaluator` (already present: Admin, Moderator, Course Creator, Tantangan Bebras Student) |
| `ab_user` / `user_profile` | 7 | 5 seed_demo accounts + `siti`, `rani` |
| `student` | 3 | budi (cub), siti (scout), rani (rover) — all `status='Active'` |
| `topic` | 6 | `pola-dan-urutan`, `berpikir-terstruktur` (cub); `dekomposisi-masalah`, `pengenalan-pola` (scout); `algoritma-dan-efisiensi`, `representasi-data` (rover) — `idx` 0/1 |
| `question` | 36 | 10 MC + 2 Essay per category; `questionCode` `TB-SGA-001…012`, `TB-PGN-…`, `TB-PNK-…`; all `status='Active'`; MC has options A–D + `correctAnswer`, Essay has a `referenceAnswer`; `creator_id` = the `creator` user |
| `event` | 5 | 3 published (deadline +30 days, 60 minutes, 10 MC questions): `event-cub-2026`, `event-scout-2026`, `event-rover-2026`; 1 draft: `event-draft` (3 questions, +14 days); 1 expired: `event-expired` (3 questions, deadline −1 day, **published=true**) |
| `event_question` | 36 | 3×10 + 2×3; `idx` order = question name order |
| `event_student` | 2 | budi→`event-cub-2026` (completed, score 70, duration 900 seconds); siti→`event-scout-2026` (in progress, `startedAt` −30 minutes) |
| `event_student_question` | 20 | pivot per attempt (FK `event_question.id`, `idx` = event order) |
| `event_student_answer` | 10 | budi's: 7 correct + 3 wrong (letters shifted +1) |
| `event_student_answer_temp` | 2 | siti's: 2 saved answers (autosave demo) |
| `practice` | 2 | budi: `student-5-seed-practice-0001` (completed, score 70, duration 600 seconds); siti: `student-6-seed-practice-0001` (in progress, started −20 minutes) |
| `practice_before_shuffle` | 20 | 10 per practice (`original_idx` = question name order) |
| `practice_question` | 20 | 10 per practice, `shuffled_idx` order = **deterministic shuffle** (`random.Random(42)` budi, `Random(7)` siti) |
| `practice_answer` | 10 | budi's: 7 correct + 3 wrong |
| `practice_answer_temp` | 3 | siti's: 3 autosaves |
| `todos` | 3 | admin: "Review question bank this week" (due +7 days), "Publish the Cub Event 2026" (completed), "Update the Rover category guide" |

**Not seeded:** `audit_logs` (the audit log is a runtime artifact — seeding would fake the audit trail), `user_profile.subscription_*` (unused), uploads.

## 5. Idempotency & Determinism

- **Idempotent**: re-running inserts **0 new rows** — every entity is looked up by its natural key first (`username`, `student.user_id`, `topic.name`, `question.name`, `event.name`, `UNIQUE(student_id, event_id)`, `UNIQUE(student_id, practice name)`).
- **Deterministic content**: question text/options/answers are fixed tuples; the practice shuffle uses seeded RNG (`Random(42)` / `Random(7)`), so `shuffled_idx` is identical on every run — the "after shuffle" column in the admin review is reproducible.
- **Fixed relative dates**: deadlines are `utcnow() + N days` (not hard-coded dates) so the pack stays valid forever; `event-expired` is always exactly 1 day in the past.
- **Single commit** at the end — a failure mid-run rolls back everything.
- **Budi's category is enforced** (`category='cub'`) even though `seed_demo` may have mutated it (the smoke test writes `siaga`-era values) — the seeder re-asserts the correct value.

## 6. Verification

```bash
cd backend
$env:SECRET_KEY = "x" * 40
.venv/Scripts/python.exe -m pytest -q        # 150/150 pass (40 auth + 105 feature + 5 seeder)
.venv/Scripts/python.exe -m scripts.seed_default   # second run: 0 rows added
.venv/Scripts/python.exe -m scripts.smoke_test      # API smoke through the seeded data
```

## 7. Porting Notes

- The seeder is the **only** path that sets `app_role` correctly (`admin`/`moderator`/`course_creator`) — see [01 §5](01-auth-student-users.md#5-role--app_role-rules). Port this behavior.
- It is also the only place that creates the `Batch Evaluator` FAB role.
- When porting, regenerate the pack in the target stack with the **same** natural keys and determinism rules so the UI states (completed/in-progress/not-started) are reachable.

---

**Back to:** [`00-master-overview.md`](00-master-overview.md) · [`FEATURES.md`](../FEATURES.md)
