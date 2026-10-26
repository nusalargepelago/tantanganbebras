# Features — Tantangan Bebras di Minimals

Entry point dokumentasi. Semua fitur di bawah **sudah diimplementasikan** di repo ini
(Flask + Vue 3), dengan pola domain berlapis (`api → dto → services → repositories →
models → presenters`) dan wire format Minimals (camelCase, error `{"message": key}`).

Detail cross-cutting & konvensi: [`00-master-overview.md`](specs/00-master-overview.md) ·
Rencana + **keputusan porting & status hazard**: [`PLAN.md`](PLAN.md).

## Implemented Features

| # | Feature | Endpoint / Route | UI | Spec |
|---|---------|------------------|----|------|
| F1 | Staff auth (register, login, logout, `/me`) | `POST /api/v1/auth/*`, `GET /me` | `/login` | [01 §2](specs/01-auth-student-users.md) |
| F2 | Student auth (self-register, login, logout, `/me`, branding) | `/api/v1/student/auth/*` | `/student-login`, `/student-register` | [01 §3](specs/01-auth-student-users.md) |
| F3 | User admin (CRUD, role-list) | `/api/v1/account/users*` | `/users`, `/users/new`, `/users/:id` | [01 §4](specs/01-auth-student-users.md) |
| F4 | Role & authorization (`app_role` + student discriminator) | startup `ensure_member_role` + `require_staff` | session guard | [01 §5](specs/01-auth-student-users.md), [00 §6](specs/00-master-overview.md) |
| F5 | Topic (chapter grouping, CRUD, reorder) | `/api/v1/topic/*` | question-editor panel | [02 §2](specs/02-topic-question.md) |
| F6 | Question bank (MC/Essay, CRUD, soft delete, restore, purge, option-list) | `/api/v1/question/*` | `/question`, `/question/new`, `/question/:name`, `/question/:name/edit` | [02 §3](specs/02-topic-question.md) |
| F7 | Question editor (autosave 3s, dirty tracking) | — | `QuestionEditor.vue` | [02 §5](specs/02-topic-question.md) |
| F8 | Practice (sheet, shuffle record, autosave, submit, scoring) | `/api/v1/student/practice/*`, `/api/v1/practice/*` (staff) | `/student/practice`, `/student/practice/start`, `/student/practice/:name` | [03](specs/03-practice.md) |
| F9 | Event (admin CRUD, question picker, publish/draft) | `/api/v1/event/*` | `/event`, `/event/new`, `/event/:name`, `/event/:name/edit`, `/event/:name/results` | [04 §2](specs/04-event.md) |
| F10 | Student event attempts (make, start, autosave, submit, results) | `/api/v1/student/event/*` | `/student/event`, `/student/event/start/:name`, `/student/event/result/:name` | [04 §3](specs/04-event.md) |
| F11 | Student management (CRUD, activate, soft delete, restore, purge) | `/api/v1/student/*` | `/student`, `/student/new`, `/student/:userId`, `/student/:userId/edit` | [05 §2](specs/05-student.md) |
| F12 | Student import (XLSX, bulk upsert, template) | `POST /student/import`, `GET .../import-template` | `/student/import` | [05 §3](specs/05-student.md) |
| F13 | Admin dashboard (7 counters + recent) & student dashboard | `/api/v1/dashboard`, `/api/v1/student/dashboard` | `/dashboard`, `/student/dashboard` | [06 §2](specs/06-supporting.md) |
| F14 | ToDo (CRUD, owner-or-admin RBAC) | `/api/v1/todos/*` | `/todos` | [06 §3](specs/06-supporting.md) |
| F15 | File upload (image, ≤5 MiB, admin) | `POST /api/v1/uploads` | TextEditor (future) | [06 §4.3](specs/06-supporting.md) |
| F16 | Default seeder (accounts, students, sample data) | `uv run python -m app.seed` | — | [07](specs/07-seeder-default-pack.md) |

## Deviations from the reference

Keputusan porting lengkap ada di [`PLAN.md`](PLAN.md) §1. Ringkasan yang paling terasa:

- **UUID PK + slug `name`** sebagai natural key untuk URL (bukan slug-PK).
- **Attempt event = snapshot** — menghilangkan mixed key-space hazard (spek §14.3).
- **`require_staff`** menutup celah RBAC spek §6.3 (student ditolak 403 di domain staff).
- **Konten soal = plain text** (`frappe-ui` tak punya `TextEditor`) — rich text defer.
- **Pagination `page`/`perPage`**, error key ikut formatter Minimals, timestamp `+00:00`.
- **Migration per domain** bernama tanggal (`20261018_<n>_<domain>.py`); `0001_initial.py` freeze.

## Cross-reference

- Hazard register (spek §14) + status tiap poin: [`PLAN.md`](PLAN.md) §5.
- Konvensi kode & layering: [`../CLAUDE.md`](../CLAUDE.md).
