# Implementation Plan — Tantangan Bebras di Minimals

Status: **DRAFT — menunggu approval reviewer.** Setiap phase butuh approval sebelum phase berikutnya dimulai.
Sumber: [`FEATURES.md`](FEATURES.md) + `specs/00–07`. Konvensi kode: [`../CLAUDE.md`](../CLAUDE.md).

---

## 0. Prinsip kerja

- **Phase = vertical slice** (backend + frontend + test + baris README) sehingga tiap phase bisa diuji
  end-to-end sebelum lanjut.
- **Alpha mindset**: schema berubah = edit `0001_initial.py` langsung (tanpa revision baru), fix di titik
  masalah, tanpa komentar kode, tanpa history numpuk.
- **Breaking change (repo/API/migrasi/dependency) → stop, minta approval** (§1).
- Ikuti pola fitur existing: layered `api → dto → services → repositories → models → presenters`,
  commit hanya di service, satu axios instance, Pinia setup-style, token frappe-ui kanonik.

---

## 1. Keputusan porting (butuh approval)

Spek 00 §14 menyiapkan hazard yang harus **diputuskan sadar**, bukan kebetulan. Berikut keputusan yang
saya ambil — semua butuh persetujuanmu:

| # | Keputusan | Alasan | Implikasi |
|---|-----------|--------|-----------|
| 1 | **PK = UUIDv7 `String(36)`** (konvensi Minimals) untuk semua tabel Tantangan Bebras; kolom `name` (slug) tetap ada sebagai **natural key UNIQUE** untuk URL `/question/:name` | CLAUDE.md pitfall 12 — PK selalu UUID; spek pakai slug-PK/int-PK | Schema beda dari spek, wire & URL tetap sesuai spek |
| 2 | **Attempt event = snapshot**: `event_student_questions` menyimpan `question_id` + `idx` sendiri (FK ke question), bukan FK ke pivot event | Menihilkan hazard spek §14.3 (mixed key-space) & aman saat event di-edit | Update event tak lagi merusak attempt lama; `answer_temp` FK → pivot attempt (satu key-space dengan yang diterima client) |
| 3 | **Pagination pakai `page`/`perPage`** (`PageIn`/`paginated_response` existing) bukan `limit`/`offset` spek | Ikuti pola repo yang sudah ada (README, FE `Pagination`/`ListFoot`) | Envelope `{items,total,page,perPage}` — superset dari spek |
| 4 | **RBAC di-**fix konsisten (spek §6.3 "no half measures"): helper baru `require_staff()` = `app_role=="admin"` **atau** akun tanpa baris `students`. Semua domain staff (topic, question, event-admin, student-admin, dashboard-admin, practice-admin, import) di-gate ini → student dapat **403** | Spek aslinya bolong (student bisa memanggil mutasi). Alpha: sekali putuskan, konsisten | Beda dari spek (spek login-only); lebih aman, tak ada 2 sumber kebenaran |
| 5 | **Konten soal = plain text (`Textarea`)**, field tetap `TEXT` | `frappe-ui@1.0.2` **tidak punya `TextEditor`** (dicek di checkout upstream); rich text + upload gambar di soal = defer | Deviasi dari spek (HTML + image upload); autosave/dirty-tracking tetap jalan; bisa dinaikkan nanti tanpa ubah schema |
| 6 | **User admin diperluas di `/api/v1/account/users`** (tambah `POST` + `DELETE` yang belum ada) — bukan bikin prefix baru `/users` | Ikuti pola fitur existing (domain account sudah punya list/get/patch) | API **additive**, bukan breaking; FE `/users` pakai endpoint account |
| 7 | **Dependency baru `openpyxl`** untuk XLSX import (P3) | Spek 05 §3 butuh read/write workbook | Ubah `pyproject.toml` (additive) + `uv sync` |
| 8 | **Error key ikut formatter Minimals** (`{field}_{message}` → `category_invalid`), bukan string panjang spek (`category_category_must_be_cub_scout_or_rover`) | Kontrak repo diuji `tests/test_contract.py`; formatter `framework/base/dto.py` sudah map enum → `invalid` | Pesan beda dari spek, bentuk `{"message": snake_case}` tetap |
| 9 | **Timestamp selalu timezone-aware + ISO `+00:00`** di semua presenter Tantangan Bebras | Menihilkan inkonsistensi spek §14.12 (ada `isoformat()` polos) | Konsisten dengan presenter existing |
| 10 | **Slug unique-suffix tetap** (`slug`, `slug-0001`…, soal: `slug-{year}-0001`) → 409 `could_not_generate_unique_name` | Spek §5 — sudah final dan FE tidak bergantung | Sama persis dengan spek |
| 11 | **Migrasi baru per domain** — `0001_initial.py` **freeze (hanya master)**. Tiap domain punya file migrasi sendiri dengan **ID tanggal**: `20261018_topic_question.py` (`revision="20261018"`, `down_revision="0001"`); di hari yang sama suffix `_2`, `_3` (chain selalu ke revisi sebelumnya). Test path tetap `db.create_all()` | Lini fitur tidak boleh mengubah histori milik master; per domain = mudah di-review & di-revert | DB existing tinggal `flask db upgrade` / `MIGRATE_ON_BOOT` — **tanpa recreate** |
| 12 | **Student auth ditaruh di domain `student`** (`api_auth.py` → prefix `/api/v1/student/auth`), bukan domain `auth` | Symmetric dengan account (domain bawahan memanggil `UserRepository` via inject) | Struktur beda dari spek (spek satukan di `auth`), endpoint sama |
| 13 | **Split endpoint practice detail**: `/student/practice/mine` + `/student/practice/<name>` (owner) vs `/practice/<name>` (staff, blueprint terpisah `staff_bp` — lihat keputusan 17) — tanpa dispatch-by-role dalam satu route | SoC: gate jelas per route, tak ada pembacaan role di service | Sedikit beda dari spek §7.1 (dispatch), FE panggil dua endpoint berbeda |
| 14 | **Rate limit default di `.env.example` naik** (mis. `RATE_LIMIT_DEFAULT=100/minute`) + override per-route sesuai spek §7 untuk route berat (autosave `120/minute`, dll) | Default `200/hour` terlalu ketat untuk UI list yang refetch per filter | **Config-only**, tidak ubah kode |
| 15 | **Naming standalone (tanpa `lms`)**: endpoint `…/lms/<domain>` → **`/api/v1/<domain>`** (satu app, tak perlu segmen disambiguasi); tabel `lms_students` → **`students`** (+ index `ix_students_*`); audit `lms/student-auth/*` → `student-auth/*`; kata/prose `LMS` → **Tantangan Bebras**. `docs/specs/*` ikut diseragamkan | App = Tantangan Bebras, bukan layanan multi-domain yang butuh prefix `lms` | **Breaking**: URL API, tabel+indeks (migrasi `20261018_2`), 53 call FE, semua test, README, docs — semua diganti & 268 test tetap hijau |
| 16 | **Login unified di `/login` (kompatibel scaffold & spek 00 §6.1)**: `AuthService.authenticate` hanya cek password + `active` — penolakan `403 use_student_login` sempat ditambahkan lalu dibatalkan atas perintah user; FE `auth.login()` revalidate `/student/auth/me` via helper `syncStudentSession()` sehingga menu ikut role (punya baris `students` → menu student, selain itu → menu staff) | Perintah user: "/login untuk admin dan student, yang membedakan keduanya adalah role"; bug menu asli (login membutakan `student=null` → akun student melihat menu staf sampai refresh) tetap diatasi di FE, bukan lewat blokir endpoint | `POST /auth/login` kembali **200** untuk akun student (`/student-login` tetap ada sebagai jalur khusus); 2 test ditulis ulang (terima akun student, wrong-password tetap 401) |
| 17 | **Segmen `admin` dihapus dari rute & endpoint**: SPA `/dashboard-admin`→`/dashboard`, `/practice-admin{,/:name}`→`/practice{,/:name}`; API `GET /dashboard/admin`→`GET /dashboard`, staff practice pindah ke blueprint baru `staff_bp` prefix `/api/v1/practice` (list `GET ""` + `GET /<name>`) | Paritas nama dengan SPA; practice staff tak lagi berada di bawah prefix `/student` (bukan role student); pemisahan role tetap lewat blueprint terpisah (keputusan 13) supaya `GET /<name>` staff vs owner tidak tabrakan | **Breaking**: 3 path API dipindah (lama mati), 1 blueprint baru, README + 2 store FE + test ikut. Approval: user ("prbaiki backend juga") |
| 18 | **Min soal practice = setting, bukan konstanta**: key `practiceMinQuestions` di tabel `settings` (helper generik `app/infra/settings.py`, default fail-safe 10), baca di `create()` (pool gate + `random.sample`); endpoint `GET /api/v1/practice/settings` (staff) + `PUT` (admin, audited `practice_settings_updated`) | Perintah user: "minimal soal configurable (setting) bukan cuman min 10" — merge `7c09f0a` (settings table) dibuatkan lebih dulu sebagai pondasi | `SHEET_SIZE` tetap jadi default saja; pesan 409 `need {n}` ikut nilai live; UI = dialog **Settings** di halaman `/practice` (admin edit, staff read-only) |
| 19 | **Statistik dashboard admin lewat endpoint baru `GET /api/v1/dashboard/stats`** (staff): `totals` (students + distinct schools non-null), siswa per sekolah (null/'' → `(No school)`, desc), pendaftaran per tahun (`extract('year', created_at)`, hanya tahun berdata), siswa per kategori (cub/scout/rover). FE `AdminDashboardView`: `NumberCard`×2 + `BarChart` per-sekolah + `DonutChart` kategori + `BarChart` per-tahun dari `frappe-ui/charts` (echarts, sudah terpasang via `frappe-ui@1.0.2`) | Perintah user: "statistik dengan chart frappe-ui — student per sekolah, pendaftaran per tahun, total seluruh sekolah dan siswa". Payload `/dashboard` lama tidak diusik (test shape eksak); "top 10 + Others" di **FE** karena `maxSeries` frappe-ui hanya men-cap series `splitBy`, bukan kategori x-axis | Murni tambahan: 1 endpoint baru, README +1 baris, spec 06 §2.3 + §6.2; tanpa migration, tanpa dependency baru |
| 20 | **Import legacy: dedupe saat import, 3 UNIQUE tetap dipakai** (`uq_practice_question`, `uq_practice_answer`, `uq_event_attempt_question`). Aturan: soal dobel dalam 1 practice → simpan satu; jawaban dobel → simpan baris `id` terbesar; practice ber-20/30/40/50/60 baris → potong ke urutan pertama | Data asli melanggar (536 / 1.489 / 321 key bentrok); **runtime tidak pernah melanggar** — practice `random.sample` tanpa replacement (`practice/services.py:94`), event snapshot dari `event_questions` yang sudah unik. Constraint memang mencerminkan aturan bisnis | **Tanpa ubah model & tanpa migrasi**; resume practice siswa lama berhenti menerima soal dobel; hasil review admin bersih |
| 21 | **Verifikasi password hybrid** — helper baru `app/infra/passwords.py`: hash diawali `$2a$`/`$2b$`/`$2y$` → `bcrypt.checkpw`, selain itu `check_password_hash` werkzeug; login sukses dengan hash bcrypt → rehash ke scrypt | werkzeug 3.1.9 hanya memuat skema `pbkdf2`+`scrypt` (dicek dari source) → semua 848 hash `$2y$10$` legacy gagal verifikasi; `bcrypt 5.0.0` **sudah** di `pyproject.toml` (dipakai API key) dan `checkpw` teruji menerima `$2y$`. Paksa-reset 848 akun ditolak | 2 call site pindah ke helper (`auth/services.py:114`, `student/services.py:110`); **tanpa dependency baru, tanpa migrasi** |
| 22 | **Konten soal legacy disimpan verbatim (HTML + base64)** di `questions.question` / `option_a..d` | 108/108 baris ber-HTML, 55 berisi `data:image/...;base64` inline, maks 851.092 karakter. Strip HTML = kehilangan gambar; keputusan §1.5 (plain text) tetap berlaku untuk konten **baru** | UI menampilkan tag apa adanya sampai ada keputusan render terpisah; `Text` muat penuh di sqlite/postgresql |
| 23 | **Target DB import: `sqlite` / `postgresql`, bukan MySQL** | `pertanyaan` maks 851KB dan `option_*` maks 69KB melebihi `TEXT` MySQL (64KB) → truncate/exception | Kalau `DATABASE_URL` mysql, kolom harus jadi `MEDIUMTEXT` dulu (keputusan terpisah, ulangi review) |
| 24 | **Import `events.published = true`** (legacy tak punya kolom itu) | 19 event legacy semuanya sudah live; kedaluwarsa dibaca dari `eventDeadline` (semua 2023) | Tanpa migrasi; state kartu event mengikuti spek (`Published` vs kedaluwarsa via deadline) |
| 25 | **Normalisasi nilai kotor saat import, bukan menampungnya di schema**: `negara` 6 varian (`Indonesia` 819, `indonesia`, `INDONESIA`, `Bali`, `Indonesi`, `indinesia`) → `Indonesia`; **durasi attempt = `updated_at − created_at`** (persis rumus spek 04 `timeLimit = int((finished − started).total_seconds())`) — string legacy `event_siswa.waktu_pengerjaan` (format `menit:detik`, diverifikasi terhadap delta: cocok ±2 detik pada 431 baris, `jam:menit` 0 cocok) **dibuang mentah-mentah** karena berisi 37 nilai junk s/d 97.348 detik + 9 negatif, padahal delta selalu sehat (median 89s, p99 1753s, maks 3946s, 0 baris >24 jam); `questions.status` `Tidak Aktif` → `status='Inactive'` (**bukan** `disabled`); `role` `Admin`→`app_role=admin`, `Volunter`→`user` | Data kotor bukan alasan menambah kolom. Delta timestamp memang sumber kebenaran yang dipakai spek; `Tidak Aktif` adalah status konten, bukan soft-delete | Transformasi murni di importer; **tanpa parser durasi**, tanpa kolom & migrasi baru |
| 26 | **Event test mode sudah ada & tercatat di sini**: `make(..., test=True)` (`app/event/services.py:233-239`) — admin (`app_role=="admin"`) **atau** staff tanpa baris `students` boleh; student ditolak `test_requires_staff`; attempt lama ber-prefix `test-` dihapus dulu | **Tidak ada di spek 04** dan belum tercatat di §1 ini — dicatat agar tidak dianggap regresi | Sudah jalan & sudah diuji; tanpa perubahan |
| 27 | **Practice test mode menyusul di phase sendiri**: flag `test` di `POST /student/practice/create`, mirror pola event (hapus practice `test-` lama, prefix `test-`, lewati gate `student_not_found`) | Admin tanpa baris `students` **tidak bisa test practice hari ini** (`practice/services.py:82` → 409 `student_not_found`); seeder memang membuat admin tanpa baris student (`app/seed.py:299`) | API **additive** (flag baru + prefix), tanpa migrasi; dijadikan phase terpisah supaya import tidak tertahan |
| 28 | **Yang sengaja TIDAK dimigrasikan**: tabel infra Laravel (`migrations` 16, `failed_jobs` 0, `password_resets` 0, `personal_access_tokens` 0), `training` (0 baris), dan kolom tanpa padanan `email_verified_at` / `remember_token` (semua NULL) + timestamp `sheet_answers`/`exams`/`sheet_questions` | Kosong, atau memang bukan milik domain ini | Tanpa kehilangan data berarti |
| 29 | **Fitur export & import = full DB backup/restore dengan format SQL dump** — keputusan desain (user, 2026-10-23): **(a)** berupa **halaman admin di UI** (endpoint + halaman, bukan CLI); **(b)** restore **boleh menimpa**, dengan **validasi statement** — hanya `BEGIN`/`COMMIT`/`DELETE FROM`/`INSERT INTO` yang menyasar tabel milik `db.metadata`, statement lain (CREATE/DROP/PRAGMA/ATTACH/UPDATE/SELECT) ditolak 400 `backup_statement_not_allowed`; **(c)** isi dump = **semua tabel aplikasi** (termasuk `settings`, `roles`, `user_roles`, `audit_logs`, `api_keys`) | Perintah user saat membuka phase ini. Validasi statement membuat restore tidak bisa jadi pintu eksekusi SQL arbitrer, dan schema tetap milik migrasi (dump tidak memuat CREATE TABLE) | Dibuka sebagai **Phase 13**; dump & restore khusus **sqlite** (dialect `iterdump` tidak dipakai — dump digenerate sendiri dari `db.metadata.sorted_tables`) |
| 30 | **Restore backup = dump penuh (semua tabel) + auto-snapshot sebelum restore; mode import "gabung" ditunda jadi phase sendiri** — keputusan (user, 2026-10-23) yang **membatalkan** arahan sebelumnya "kecualikan tabel `0001_initial` / domain saja". Snapshot = FE unduh `GET /backup/export` lebih dulu, gagal → restore batal. Mode merge (additive, upsert by natural key, konten referensi `topics`/`questions`/`events`/`event_questions` saja, tak menyentuh users/settings/audit/riwayat) = phase baru | `students.user_id`, `practices.student_id`, `event_attempts.student_id` semuanya FK **NOT NULL → `users.id`**: mengecualikan `users` = siswa yatim (sqlite lolos tapi tak bisa login; Postgres gagal FK). Restore yang utuh justru **butuh** `users` ikut — escape hatch-nya snapshot, bukan scope terdegradasi. Praktik CMS lain: restore penuh + snapshot (cPanel, backup WP), import terpisah & additive (WXR, `loaddata`, Ghost) | Snapshot di FE → **nol perubahan backend** (endpoint, README, `test_docs` tak berubah); file `minimals-pre-restore-YYYYMMDD-HHMMSS.sql`; i18n `backup.snapshotFailed` baru |

Belum ada yang dijalankan sebelum §1 di-approve.

---

## 1b. Import data legacy — `D:\nush3418_tantanganbebras.sql`

Dump MySQL/Laravel 17,6 MB, 17 tabel, referensial **bersih** (0 orphan di 15 FK), tabrakan
email/username `siswa`×`users` = **0**. Baris domain: 841 siswa + 7 staff + 108 soal + 19 event
+ 1.404 attempt + 149 pivot event + 13.728 snapshot attempt + 12.642 jawaban event + 3.195 practice
+ 31.950 soal practice + 31.950 before-shuffle + 24.709 jawaban practice.

| Legacy | → Target | Transformasi wajib |
|---|---|---|
| `siswa` (841) | `users` + `students` | `nama_depan`→`first_name`, `nama_akhir`→`last_name`, `full_name` = gabung; `kategori`→`cub/scout/rover`; `status Aktif`→`Active`; `sekolah/kota/negara`→`school/city/country`; password `$2y$` dipertahankan (§1.21) |
| `users` (7) | `users` + `roles`/`user_roles` | `username` = `email` (unik, tabrakan 0); `name`→`first_name` (+`full_name`); `role`→`app_role` (§1.25); `Member` role di-seed `ensure_member_role()` |
| `questions` (108) | `questions` | **`name` digenerate** (`kode_soal` hanya 72 distinct/108 → suffix unik); enum 4 kolom dipetakan (spek 00 §11); `topic_id`/`creator_id` NULL; `disabled=false` |
| `event` (19) | `events` | **`name` digenerate** (15 distinct/19 → suffix); `waktu_pengerjaan` (menit)→`time_limit`; `batas_event`→`event_deadline`; `published=true` (§1.24); `description`/`creator_id` NULL |
| `event_siswa` (1.404) | `event_attempts` | **`name` digenerate**; `nilai`→`score`; `created_at`→`started_at`, `updated_at`→`finished_at`, selisihnya→`time_limit` detik (§1.25 — string `waktu_pengerjaan` dibuang); **tanpa UNIQUE(student,event)** → 312 pasangan duplikat aman; 47 attempt tanpa soal tetap diimpor |
| `exams` (149) | `event_questions` | cocok persis (unik per event,question); **`idx` = urutan `exams.id`** |
| `sheet_event_siswa` (13.728) | `event_attempt_questions` | **dedupe** 321 key bentrok (§1.20) → **13.267**; **`idx` = urutan `id`** |
| `sheet_event_answers` (12.642) | `event_attempt_answers` | FK ke `event_attempt_questions` via **kunci `(attempt, soal)`** — bukan `(attempt, exam)`: ada jawaban menunjuk exam di luar sheet yang soalnya tetap masuk lewat exam lain, jadi tetap sah. Dup → `id` terbesar; hanya jawaban yang **soalnya tidak ada di snapshot** yang dibuang (**2**) → **12.247** |
| `exercises` (3.195) | `practices` | **`name` digenerate**; **`category` diturunkan dari siswa**; `nilai`→`score`; `created_at`→`started_at`, `updated_at`→`finished_at`; `time_limit` NULL (legacy tak punya durasi practice) |
| `sheet_questions` (31.950) | `practice_questions` | **dedupe** 536 key (§1.20) → 31.134; **potong sheet ke 10 soal** (1 practice berisi 14) → **31.130**; **`shuffled_idx` = urutan `id`** |
| `sheet_before_shuffle` (31.950) | `practice_before_shuffle` | **dedupe + potong mengikuti `practice_questions`** supaya tampilan before/after seimbang → 31.130; **`original_idx` = urutan `id`** |
| `sheet_answers` (24.709) | `practice_answers` | **dedupe** 1.489 key (id terbesar menang) → 20.936; **buang 69 jawaban yatim** yang soalnya tak pernah ada di sheet legacy (10 practice) → **20.867**, meniru invariant runtime `submit()` (jawaban ⊆ sheet) |

**Jumlah baris target setelah dedupe** — angka yang diasumsikan `tests/test_import_legacy.py`:

| users | students | questions | events | event_questions | event_attempts | event_attempt_questions | event_attempt_answers |
|---|---|---|---|---|---|---|---|
| 848 | 841 | 108 | 19 | 149 | 1.404 | 13.267 | 12.247 |

| practices | practice_questions | practice_before_shuffle | practice_answers |
|---|---|---|---|
| 3.195 | 31.130 | 31.130 | 20.867 |

- **Remap ID**: `bigint` → UUIDv7. Delapan tabel di atas saling rujuk → bangun dict
  `legacy_id → uuid` per tabel di memori (~5.700 baris) saat import.
- **Order**: 4 kolom idx turunan (`event_questions.idx`, `event_attempt_questions.idx`,
  `practice_questions.shuffled_idx`, `practice_before_shuffle.original_idx`) → `ORDER BY id` lama.
- **Jalur**: satu CLI `uv run python -m app.import_legacy --dump <path>` — idempoten
  (skip kalau tabel target sudah terisi), satu transaksi, tanpa commit di luar service.
- **Target DB**: sqlite/postgresql (§1.23).

---

## 2. Arsitektur target

### 2.1 Domain backend baru

| Domain | Blueprint prefix | Spesifikasi |
|---|---|---|
| `app/topic/` | `/api/v1/topic` | 02 §2 — list/get/create/update/delete/reorder (hard delete) |
| `app/question/` | `/api/v1/question` | 02 §3 — list(+`total`)/option-list/get/create/update/soft-delete/restore/purge |
| `app/student/` | `/api/v1/student` + `api_auth.py` (`…/auth`) + `api_import.py` (`…/import`, `/import-template`) + `api_dashboard.py` (`…/dashboard`) | 01 §3, 05 |
| `app/practice/` | `/api/v1/student/practice` + `staff_bp` (`/api/v1/practice`) | 03 — create/start/answer-temp/store/mine/<name> (student), list/<name> (staff) |
| `app/event/` | `/api/v1/event` + `api_student.py` (`/api/v1/student/event`) | 04 |
| `app/dashboard/` | `/api/v1/dashboard` | 06 §2 — root route (staff); route student pindah ke `app/student/api_dashboard.py` |
| `app/todos/` | `/api/v1/todos` | 06 §3 — CRUD + owner-or-admin |

Setiap domain = 7 file wajib (`__init__`, `api`, `dto`, `models`, `presenters`, `repositories`, `services`)
+ `api_*.py` untuk blueprint tambahan (pola `account/api_key_api.py`). Wajib: model di-import di
`create_app.py`, blueprint didaftarkan **sebelum** `register_spa`, baris endpoint ditambah ke tabel
`README.md` (`test_docs.py` menjaga), test di `tests/test_<domain>.py`.

### 2.2 Shared helpers lintas domain (baru, di `app/infra/`)

| File | Isi | Dipakai oleh |
|---|---|---|
| `enums.py` | `CATEGORIES (cub/scout/rover)`, `DIFFICULTIES`, `QUESTION_TYPES`, `STATUSES` | topic, question, event, student, practice |
| `naming.py` | `slugify()` + `next_name()` (suffix `-0001`…, tahun untuk question) | topic, question, event |
| `scoring.py` | `POINTS_PER_CORRECT=10`, `SHEET_SIZE=10`, `is_correct(question, answer)` | practice, event |
| `presenters.py` | `UtcPresenterBase` — normalisasi timestamp naive → ISO `+00:00` di wire | semua presenter Tantangan Bebras (keputusan §1.9) |
| `roles.py` (tambah) | `require_staff()` (keputusan §1.4) | semua domain staff |

### 2.3 Guard matrix (final)

| Kelompok endpoint | Gate |
|---|---|
| topic, question, event (admin), student (admin+import), practice admin (`/`, `/admin/<name>`), dashboard admin | `@login_required` + `require_staff()` → 403 `forbidden` |
| `student/auth` (register/login/branding), `csrf`, `health`, `uploads` | public / existing |
| practice student (`create/start/answer-temp/store/mine/<name>`) | login + baris `students` wajib (ada → `404 student_not_found` / 409 sesuai spek) |
| `student/event` (list/make/start/answer-temp/store) | login + baris `students` (list tanpa student → `200 {items:[]}` sesuai spek 04 §3.1) |
| `student/dashboard` | login + baris student, else 404 `student_not_found` |
| todos | `login_required` + `require_owner_or_role(owner, "admin")` (existing) |
| account users/roles | `require_role("admin")` (existing, tak diubah) |

`require_staff()` = authenticated **dan** (`app_role == "admin"` **atau** akun tanpa baris `students`).

### 2.4 Wire format

- Ikut kontrak repo: objek telanjang untuk single/mutasi, `{items}` untuk list, `{items,total,page,perPage}`
  untuk paginated, `204` no-content, error `{"message":"<snake_case_key>"}` — camelCase via alias eksplisit.
- Error status mengikuti tabel spek per endpoint (404 not-found, 409 conflict/state, 400 DTO) —
  `NotFound/Conflict/InvalidOperation/ValidationFailed` dari `framework/exceptions` (service raise,
  bukan return response).
- `q`/filter list pakai query params camelCase (`difficultyLevel`, `includeDisabled`) sesuai spek §02 §4.

### 2.5 Schema (tabel per domain, migrasi baru bernama tanggal — `0001_initial.py` freeze)

| Phase | File migrasi | Tabel baru | Catatan |
|---|---|---|---|
| P1 | `20261018_topic_question.py` | `topics`, `questions` | topic: unique `name`; question: `disabled`+`disabled_at`+index, index `(category,status)`, `(topic_id)` |
| P3 | `20261018_2_student.py` | `students` | PK `user_id` → `users.id` CASCADE; soft delete sinkron `users.active` |
| P5 | `20261018_3_practice.py` | `practices`, `practice_questions`, `practice_before_shuffle`, `practice_answers`, `practice_answer_temps` | UNIQUE(practice,question) di 3 tabel; FK RESTRICT ke question |
| P7 | `20261018_4_event.py` | `events`, `event_questions`, `event_attempts`, `event_attempt_questions`, `event_attempt_answers`, `event_attempt_answer_temps` | UNIQUE(student,event) di attempt; attempt pivot = **snapshot** (keputusan §1.2) |
| P9 | `20261018_5_todos.py` | `todos` | hard delete |

(Date suffix `_N` mengikuti urutan kerja aktual — nama file fleksibel, chain `down_revision` yang menentukan urutan.)

State machines (soft delete, published/draft, terminal attempt) persis spek 00 §4.

### 2.6 Frontend features

| Feature folder | Routes | Phase |
|---|---|---|
| `question` | `/question`, `/question/new`, `/question/:name`, `/question/:name/edit`, `/question-editor` | P2 |
| `auth` (tambah) | `/student-login`, `/student-register` + state `student` di store | P4 |
| `student` | `/student`, `/student/new`, `/student/:userId`, `/student/:userId/edit`, `/student/import` | P4 |
| `users` | `/users`, `/users/new`, `/users/:id`, `/users/:id/edit` (endpoint account) | P4 |
| `practice` | `/student/practice`, `/student/practice/start`, `/student/practice/:name`, `/practice`, `/practice/:name` | P6 |
| `event` | `/event`, `/event/new`, `/event/:name`, `/event/:name/edit`, `/event/:name/results` | P8 |
| `event-student` | `/student/event`, `/student/event/start/:name`, `/student/event/result/:name` | P8 |
| `dashboard` (ganti placeholder) | `/dashboard`, `/student/dashboard`, `/` (home quick-links) | P9 |
| `todos` | `/todos` | P9 |

Design system kanonik (skill `polish`):

- **Page**: `PageHeader > PageBreadcrumbs + Button solid` → `div.mx-auto.max-w-6xl.space-y-4.px-5.py-6`.
- **List**: `ListToolbar v-model:search/per-page` (+ slot `Select`/`Combobox` filter server-side) →
  `useListControls` → state 3-way (`Skeleton×6` / empty state icon+CTA / frappe-ui `List` + `ListHead`
  + `ListRows` + `ListCell`) → `ListFoot` → `ErrorMessage` di bawah.
- **Dialog kecil** (topic modal, todo modal): `Dialog v-model:open` + `actions` array
  (`Batal` outline / `Simpan` solid), `watch(open) → load()`, `FormControl`/`Combobox`, `canSave`
  computed, submit → store → `toast.*` → `emit('saved')`.
- **Form page besar** (question/event/student/users): sticky header + badge `Unsaved`, section,
  validasi lokal `touched`, inline `ErrorMessage`, `Button :loading`.
- **Imperatif**: `dialog.danger/confirm/prompt` untuk destructive/leave-guard, `toast.success/error`
  setelah await, tidak ada toast untuk state.
- **Runner** (practice/event): `shared/composables/useCountdown.ts` + `shared/components/QuizRunnerShell.vue`
  (pager, MC radio, essay textarea, autosave fire-and-forget, chip countdown, leave guard) — dibangun di
  P6, dipakai ulang P8.
- **Nav**: section sidebar di `AppShell.vue` di-gate `auth.student`/`auth.user.appRole`
  (staff: Question, Event, Student, Practice Review, Todos, Dashboard; student: Practice, Events);
  route meta `requiresStaff` dideklarasikan di `meta.d.ts` dan dicek `guard.ts` (FE hint — backend tetap
  otoritatif).
- **Aturan #0**: tidak ada `<input>/<button>/<select>/<textarea>` native; ikon `lucide-*` string;
  token `text-*-semibold`, `rounded-6`, `bg-surface-elevation-2`, `text-ink-gray-*`.

---

## 3. Phase plan

> **DoD umum tiap phase**: `uv run pytest` hijau · `uv run ruff check .` bersih · (FE) `yarn typecheck`
> + `yarn build` sukses · baris README endpoint sinkron (`test_docs.py`) · smoke checklist per phase
> lulus · **lalu minta approval sebelum phase berikutnya.**

### Phase 1 — Topic & Question Bank (backend)

- **Scope**: shared helpers (`infra/enums.py`, `infra/naming.py`, `require_staff`), domain `topic` dan
  `question` lengkap (CRUD, soft delete/restore/purge, reorder, `option-list`, filter `q/category/
  difficultyLevel/topic/includeDisabled`, `total` akurat), migrasi tabel P1, README, audit
  (`topic_created/updated/deleted/reordered`, `question_created/…/purged`), rate limit per-route spek §7.
- **Deliverables**: `app/topic/` (7), `app/question/` (7), edit `create_app.py`, edit `0001_initial.py`,
  edit `README.md`, `tests/test_topic.py`, `tests/test_question.py`.
- **Test mandiri**: pytest CRUD → slug unik (suffix `-0001`, soal pakai `{year}`), soft-delete tidak
  muncul di list default tapi detail tetap bisa, restore/purge, guard 403 untuk (simulasi) student,
  DTO error key, pagination `{items,total,page,perPage}`.
- **Tidak termasuk**: UI apa pun.
- ⚠ **Migrasi (keputusan §1.11)**: tabel baru nambah di `0001_initial.py` — DB dev lama harus recreate.

### Phase 2 — Question Bank & Topic (frontend)

- **Scope**: list question (filter server-side debounce 200ms, search client-side), form create/edit
  (MC/Essay conditional, validasi lokal), detail, **editor 3-kolom** (`?question=` selection, outline
  topik+soal, autosave debounce 3s + dirty tracking + badge Saving/Saved/Error, panel settings),
  modal topic (create/edit, delete dengan konfirmasi "detach questions"), delete question (soft).
- **Deliverables**: `features/question/{routes,store,validation}.ts` + `views/*` + `components/
  {QuestionOutline,TopicRow,TopicModal,QuestionModal}.vue`, daftarkan route, `meta.d.ts` + `guard.ts`
  (`requiresStaff`), `app/breadcrumbs.ts`, nav sidebar P2, `tests/test_spa.py` tetap hijau.
- **Test mandiri**: `yarn typecheck/build`, smoke browser: buat topic → buat soal → edit di editor
  (autosave jalan, reload tak hilang) → soft delete → tampil di list `includeDisabled`.

### Phase 3 — Student domain (backend)

- **Scope**: student-auth (branding `GET /login`, register → `status=Inactive`, login cek
  `active`+`disabled`, logout, `me`), student CRUD admin (list `+total`, create, get, patch, soft
  delete sinkron `users.active`, restore, activate, purge), XLSX import + template (file-level errors
  sebagai `errors[]`, tak pernah 4xx untuk workbook rusak), **tutup gap user-admin** (`POST/DELETE
  `/account/users`), rate limit (import `5/minute`, autosave-style lain sesuai spek), audit lengkap.
- **Deliverables**: `app/student/` (7 + `api_auth.py` + `api_import.py`), tambal `app/account`
  (dto/service/api/tests), `pyproject.toml` += `openpyxl`, migrasi tabel `students`, README,
  `tests/test_student.py` (+ auth/account test extension).
- **Test mandiri**: register → login (Inactive belum dicek spek: login hanya cek `active/disabled`) →
  activate → login ok; soft delete memblokir login student; import sukses/partial/error per baris;
  duplicate username/email → 409; guard staff pada CRUD.
- ⚠ **Dependency baru + migrasi** (keputusan §1.7, §1.11).

### Phase 4 — People & Auth (frontend)

- **Scope**: halaman student login/register (branding dari API), auth store dual-session
  (revalidate `/auth/me` → fallback `/student/auth/me`), student management (list status default
  `Active`, form, detail, activate, delete dialog, import page `FormData` **tanpa** bug
  `JSON.stringify` spek §5.4), user admin (list/form/detail/reset-password via `dialog.prompt`),
  sidebar role-aware (staff vs student) + guard.
- **Deliverables**: `features/auth/views/Student{Login,Register}View.vue` + store extension,
  `features/student/*`, `features/users/*`, AppShell nav, router, breadcrumbs, tests SPA.
- **Test mandiri**: smoke — staff login lihat menu staff; student login lihat menu student; student
  buka `/question` → redirect; import xlsx nyata (file terkirim, hasil `inserted/updated/errors`).

### Phase 5 — Practice (backend)

- **Scope**: `infra/scoring.py`, practice create (pool kategori, min 10 → 409 dinamis, shuffle +
  before/after recording), resume `GET /start`, autosave upsert (guard terminal → 404), submit+skor
  (10×benar, essay 0, `timeLimit` detik), detail split (mine/owner vs admin), list mine/admin, audit,
  rate limit (`answer-temp 120/minute`).
- **Deliverables**: `app/practice/` (7), `app/infra/scoring.py`, migrasi 5 tabel, README,
  `tests/test_practice.py`.
- **Test mandiri**: create → autosave → submit → skor benar (MC beda huruf besar/kecil, kosong = salah,
  essay = 0); submit dua kali → 409; `answer-temp` setelah submit → 404; non-owner → 404; insufficient
  pool → 409 `insufficient_question_in_category: have {n}, need 10`.

### Phase 6 — Practice (frontend)

- **Scope**: student list (PracticeCard gradient per kategori, status badge, duration), **runner**
  (countdown `timeLimit ?? 30` auto-submit, pager numeric, autosave fire-and-forget, leave guard
  `dialog.confirm` Save & Leave, `beforeunload`), result (skor + detail jawaban), admin list + detail
  (before vs after shuffle) — termasuk komponen **shared** `useCountdown` + `QuizRunnerShell` untuk P8.
- **Deliverables**: `features/practice/*`, `shared/composables/useCountdown.ts`,
  `shared/components/QuizRunnerShell.vue`, nav, breadcrumbs, smoke.
- **Test mandiri**: browser — start → jawab (autosave, badge terisi) → reload → lanjut → submit →
  nilai tampil; admin review shuffle konsisten.

### Phase 7 — Event (backend)

- **Scope**: event admin CRUD (validasi `questionsId`: exist/category/disabled, slug, soft
  delete/restore/purge, `questionCount` tanpa N+1, filter `published/includeDisabled`, results
  `score DESC NULLS LAST`), event-student (candidate list + `categoryMatch/alreadyAttempted`, `make`
  idempotent + guards 409, `start` snapshot resolve, autosave, store+skor), **schema snapshot
  (keputusan §1.2)**, audit, rate limit.
- **Deliverables**: `app/event/` (7 + `api_student.py`), migrasi 6 tabel, README,
  `tests/test_event.py`, `tests/test_event_student.py`.
- **Test mandiri**: create dengan kategori beda → 409 `question_category_mismatch`; make kedua kali →
  attempt lama (idempotent); expired/draft/disabled → 409; autosave FK valid di SQLite & Postgres
  (lintas key-space tidak ada lagi); edit event (ganti soal) tak merusak attempt lama.

### Phase 8 — Event (frontend)

- **Scope**: admin list (filter category/published server-side, row action Play untuk staff yang punya
  baris student), form (question picker terfilter kategori+aktif, `datetime-local` deadline), detail,
  results; student list `EventCard` (4 state tombol eksklusif + category-mismatch badge), **runner**
  (reuse `QuizRunnerShell`, countdown `timeLimit ?? 0`), result page.
- **Deliverables**: `features/event/*`, `features/event-student/*`, nav, breadcrumbs, smoke.
- **Test mandiri**: semua state kartu (not started/in progress/completed/mismatch), runner autosave +
  submit + leave guard, hasil tampil.

### Phase 9 — Dashboard, Todos & Home (backend + frontend)

- **Scope**: `GET /dashboard` (7 counter + recent events/students, `questionCount` tanpa N+1),
  `GET /student/dashboard` (4 key + last practice/event), todos CRUD (admin lihat semua /
  owner-or-admin, `dueDate` validasi), home quick-links sesuai role (spek 06 §6.1), nav + breadcrumbs.
- **Deliverables**: `app/dashboard/` (7), `app/todos/` (7), migrasi `todos`, FE `features/dashboard`
  (ganti placeholder) + `features/users` nav review + `features/todos`, README, tests.
- **Test mandiri**: counter akurat terhadap data hasil phase sebelumnya; todos RBAC 403 non-owner;
  dashboard student 404 tanpa baris student.

### Phase 10 — Seeder & finalisasi docs

- **Scope**: CLI seeder idempoten (`uv run python -m app.seed`): akun staff + 3 student per kategori +
  6 topik + 36 soal + 5 event + attempt/practice sample (Completed / In Progress / belum mulai) +
  todos, deterministik (RNG seeded, deadline relatif `utcnow()+N`), single commit; perbarui
  `FEATURES.md` (status per fitur di repo ini), final sinkron README ↔ `url_map`, review akhir
  hazard register (spek 00 §14) → tandai mana yang direproduksi/diperbaiki di `docs/`.
- **Deliverables**: `app/seed.py`, README/FEATURES update, `tests/test_seed.py` (idempoten: run 2× →
  0 row baru).
- **Test mandiri**: fresh DB → migrate → seed → smoke seluruh alur staff & student dari data seed.

### Phase 11 — Import data legacy (dump MySQL → schema sekarang)

- **Scope**: helper `app/infra/passwords.py` (hybrid verify + rehash, §1.21) dan perbaiki 2 call
  site login; CLI `app/import_legacy.py` (`uv run python -m app.import_legacy --dump <path>`)
  yang menjalankan pemetaan §1b — dict remap ID bigint→UUIDv7 di memori, generate `name` unik di 4
  tabel, derive `practices.category` + 4 kolom `idx`, map enum (§1.15), normalisasi `negara`/
  durasi (§1.25), **dedupe 3 UNIQUE** (§1.20), `published=true` (§1.24); idempoten & satu transaksi.
- **Deliverables**: `app/infra/passwords.py`, `app/import_legacy.py`, 2 edit call site,
  `tests/test_import_legacy.py`, baris §1b/§1.20–28 di `PLAN.md` (sudah ditulis di Phase A).
- **Test mandiri**: DB bersih → migrate → import → hitung row per tabel = angka §1b · login legacy
  memakai password `$2y$` lama (berhasil) dan password salah (ditolak) · praktik resume tak
  mengembalikan soal dobel · review admin menampilkan practice/event tanpa duplikat ·
  `uv run pytest` + `ruff` hijau. **Tanpa endpoint HTTP baru → tanpa baris README.**
- ⚠ **Tanpa migrasi & tanpa dependency baru** (keputusan §1.20, §1.21).

### Phase 12 — Practice test mode untuk staff ✅ selesai

- **Scope**: flag `test` di `POST /api/v1/student/practice/create` mengikuti pola event persis
  (keputusan §1.27) — query param `?test=1&category=cub`, DTO `CreateIn` divalidasi dari
  `request.args` (pola `PageIn`); lewati gate `student_not_found`, tolak student dengan 403
  `test_requires_staff`, hapus practice test lama (ikut 4 tabel anak), prefix nama `test-`.
  `category` wajib hanya untuk akun **tanpa** baris `students` (400 `category_required`;
  nilai di luar enum → 400 `category_invalid` dari Literal DTO).
- **Perilaku ikutan yang terpakai diubah**: `start()` kini mengambil praktik **belum selesai
  terbaru** (`active_for_student`, `finished_at IS NULL`) — kalau tidak, praktik test yang sudah
  disubmenutupi resume practice nyata. `mine` dan list staff menyaring `test-%` (mirror spek event
  yang menyembunyikan attempt test), `start()` tetap memakainya supaya runner bisa membuka sheet test.
- **Deliverables**: `app/practice/{dto,api,services,repositories}.py`, `app/practice/__init__.py`,
  `frontend/src/features/practice/{store.ts,views/PracticeAdminDetailPage.vue}` (tombol **Test Quiz**
  di halaman review, `lucide-play`, sama seperti `EventDetailPage`), kunci i18n
  `practice.testQuiz`/`practice.testFailed` di `en.json`+`id.json`, 8 test di `tests/test_practice.py`.
- **Perbaikan lanjutan (disetujui user setelah Phase 12)**: `EventRepository.delete_test_attempts`
  kini juga menghapus `EventAttemptAnswer` (lewat id `EventAttemptQuestion` milik attempt test) dan
  `EventAttemptAnswerTemp` — sebelumnya hanya 2 dari 4 tabel anak, jadi attempt test yang pernah
  dijawab menyisakan baris yatim (tidak memicu error karena query di-filter per attempt name, tapi
  tetap sampah). Ditutup oleh `test_replacing_test_attempt_leaves_no_orphan_rows`.
  Pola 4-tabel ini sekarang sama dengan `PracticeRepository.delete_test_practices`.
- **Test mandiri**: ✅ admin tanpa baris student → create `test-` sukses & bisa `start()` (10 soal);
  student biasa → 403 `test_requires_staff`; tanpa `category` → 400; `category=nope` → 400
  `category_invalid`; practice non-test tetap menolak admin (409 `student_not_found`); test kedua
  menggantikan test pertama tanpa menyisakan 10 baris `practice_questions` yatim; list staff tak
  menampilkan test; `start()` jatuh ke practice belum-selesai lama. `uv run pytest` **334 hijau**,
  `ruff` bersih, `yarn typecheck` + `yarn build` sukses.

### Phase 13 — Backup export & restore (admin UI) ✅ selesai

- **Endpoint** — blueprint `backup` di `app/infra/backup.py`, prefix `/api/v1/backup`, gate
  `require_role("admin")`, CSRF tetap aktif (bukan blueprint exempt):

  | Method | Path | Perilaku |
  |---|---|---|
  | GET | `/api/v1/backup/export` | Balik `minimals-backup-YYYYMMDD-HHMMSS.sql` sebagai attachment; audit `backup_exported` |
  | POST | `/api/v1/backup/import` | Multipart `file` (`.sql`), rate `2/minute`; validasi → eksekusi satu transaksi → `{"tables", "rows"}`; audit `backup_restored` |

- **Format dump** (dibuat sendiri, bukan `sqlite3.iterdump()`): komentar `-- minimals-backup v1`,
  lalu `BEGIN TRANSACTION`, **`DELETE FROM "<tabel>"` untuk semua tabel dalam urutan dependensi
  terbalik** (anak dulu — `db.metadata.sorted_tables` dibalik), **`INSERT INTO` untuk semua tabel
  dalam urutan dependensi** (orang tua dulu), `COMMIT`. Karena dump sendiri yang menghapus, restore
  otomatis menimpa data lama; tabel yang tidak ada di dump (skema lebih baru) dibiarkan utuh.
  Nilai dibaca **mentah** via `SELECT *` (bukan lewat ORM) supaya round-trip identik; string di-escape
  ganda (`'` → `''`), `NULL`/angka apa adanya. Kunci tabel dari `db.metadata` — tidak ada string
  nama tabel dari file yang dieksekusi.
- **Validasi**: setiap statement dipisah dengan pemisah yang sadar kutip (`''` — data soal
  berisi newline), lalu dicek prefiksnya terhadap daftar putih di atas. Gagal → 400
  `backup_statement_not_allowed`, file kosong → 400 `backup_empty_file`, tanpa bagian `file` →
  400 `file_required` (pola import siswa). Eksekusi **satu transaksi** — gagal di tengah → rollback,
  DB tidak berubah. Bukan sqlite → 422 `backup_unsupported_database`.
- **Config**: `MAX_CONTENT_LENGTH` default naik **1MB → 64MB** (tetap env-overridable). Wajib:
  dump penuh dengan data legacy saja sudah ~30MB. Sekaligus menutup mismatch lama — upload gambar
  diizinkan 5MiB tapi limit global hanya 1MB. ⚠ Satu-satunya perubahan default keamanan di phase ini.
- **Frontend**: rute `/backup` (`requiresAdmin` — sudah tersedia di `meta.d.ts` + `guard.ts`), nav
  admin-only di `AppShell.vue` (`v-if="auth.isAdmin"`), halaman `features/backup/` dengan dua kartu:
  **Export** (tombol `href` langsung ke endpoint — pola unduh template `StudentImportPage.vue:103`)
  dan **Import** (input `.sql` tersembunyi + `FormData`, konfirmasi `dialog.danger` sebelum restore
  karena menimpa data). Kunci i18n `backup.*` di `en.json` + `id.json`, baris README +2.
- **Deliverables**: `app/infra/backup.py`, `framework/infra/config.py` (limit), `app/create_app.py`
  (registrasi blueprint sebelum `register_spa`), `README.md` +2 baris, `frontend/src/features/backup/*`,
  AppShell nav, `tests/test_backup.py`.
- **Test mandiri**: export butuh admin (401/403) · balikan punya header `-- minimals-backup v1` dan
  memuat INSERT tabel berisi · **round-trip**: ubah data → export → rusakkan data → import → data
  kembali persis · import menolak `DROP TABLE`/`PRAGMA` dengan 400 `backup_statement_not_allowed`
  dan DB tidak berubah · import tanpa `file` → 400 `file_required` · `uv run pytest` hijau, `ruff`
  bersih, `yarn typecheck` + `yarn build` sukses, `test_docs.py` hijau (README ↔ `url_map`).
- **Hasil verifikasi nyata** (dump legacy 30,2MB / 116.054 baris / 21 tabel di sqlite): export
  **1,96 detik** · parse+validasi **7,6 detik** · restore **8,5 detik** · round-trip COUNT semua
  tabel **MATCH** (termasuk 20.867 `practice_answers` yang sengaja dihapus sebelum restore).
  `uv run pytest` **347 hijau** (13 test backup), `ruff` bersih, `yarn typecheck` + `yarn build` sukses.
- **Jebakan yang ketemu & sudah ditambal**: dump berisi teks soal yang memuat `?` dan `:_nama`
  (`"Maaf tdk tau \_(?)_/"`) — `sqlalchemy.text()` menganggapnya **bind parameter**, jadi restore
  gagal `InterfaceError 21`. Solusinya `connection.exec_driver_sql(...)` (kirim SQL apa adanya);
  karena itu juga pemisah statement harus sadar kutip (`''`) dan sadar komentar `--`, atau teks
  berisi `;` akan terpotong jadi statement terlarang. Keduanya kini dicakup test
  (`test_round_trip_preserves_quotes_and_sql_in_text`, `test_import_rejects_statement_after_semicolon`).
- **Auto-snapshot sebelum restore** (lanjutan keputusan §1.30): `store.restore()` menjalankan
  `takeSnapshot()` → `GET /backup/export` sebagai blob → unduh `minimals-pre-restore-<stamp>.sql`
  **sebelum** `POST /backup/import`; snapshot gagal → `error.value` diisi (`backup.snapshotFailed`)
  dan import **tidak pernah dikirim**, `finally` melepas `restoring`. Nol perubahan backend — endpoint,
  README, `test_docs` tak berubah; copy `importDesc` + `confirmMessage` menyebut snapshot, kunci baru
  `backup.snapshotFailed` (en + id).

### Dependensi antar phase

```
P1 → P2 → P4(nav)          P3 → P4
P1+P3 → P5 → P6            P1+P3 → P7 → P8 (reuse runner P6)
P3+P5+P7 → P9              semua → P10 → P11 → P12 → P13
```

Phase bisa di-review/merge per urutan; P5 & P3 paralel kalau mau (tak saling kunci).

---

## 4. Test strategy

- **Backend**: pytest fixture existing (`app`, `client`, `member`, `admin`, `csrf_client`) — tiap phase
  tambah `tests/test_<domain>.py` (happy path, guard 401/403, kontrak error & status, edge: slug bentrok,
  terminal state, ownership). `test_docs.py` menjaga README ↔ `url_map`.
- **Frontend**: `yarn typecheck` + `yarn build` (tak ada test runner FE) + smoke checklist per phase
  di browser (light **dan** dark mode untuk halaman baru).
- **Lint**: `uv run ruff check .` tiap phase.
- **Kontrak**: `tests/test_contract.py` tetap acuan wire format — jangan ubah envelope existing.

## 5. Hazard register (spek 00 §14) → status

| # | Hazard | Status di port ini |
|---|---|---|
| 1 | RBAC lemah pada mutasi Tantangan Bebras | **Diperbaiki** — `require_staff()` (keputusan §1.4) |
| 2 | `app_role` vs FAB role dua sumber | **Dihilangkan** — hanya `users.app_role` + keberadaan baris student; tanpa FAB role names |
| 3 | Mixed key-space `eventQuestionId` | **Diperbaiki** — snapshot attempt (keputusan §1.2) |
| 4 | Naive vs aware datetime | **Diperbaiki** — semua `DateTime(timezone=True)` |
| 5 | Status code tak konsisten | **Diikuti spek per endpoint** (tabel error per domain) — kecuali split endpoint practice (keputusan §1.13) |
| 6 | `QuestionUpdate` tanpa validasi bisnis transisi MC↔Essay | **Diperbaiki** — model validator jalan juga di update saat field terkait berubah |
| 7 | `total` ≠ `items` di question list | **Diperbaiki** — `total` ikut semua filter |
| 8 | Attempt PK timestamp → collision 500 | **Dihilangkan** — PK UUIDv7 (keputusan §1.1) |
| 9 | Time limit tak di-enforce backend | **Direproduksi sadar** (spek: client-only deadline) + auto-submit FE |
| 10 | N+1 questionCount / offset setelah cap 500 | **Diperbaiki** — count ter-agregasi, slicing di query |
| 11 | Admin login ignore `active`; hard delete orphan | **Diperbaiki** untuk cek `active` (staff login `AuthService` menolak `active=False`). **Direproduksi** untuk orphan hard-delete user-admin (mengandalkan aksi FK — SQLite tanpa enforce menghasilkan orphan sesuai spek; di Postgres CASCADE/SET NULL bersih) |
| 12 | Inkonsistensi timestamp wire | **Diperbaiki** — selalu `+00:00` (keputusan §1.9) |
| 13 | SPA catch-all telan 404 API | **Direproduksi** (urutan `register_spa` existing) — tanpa perubahan |
| 14 | Dead code | **Tidak dibawa** |
