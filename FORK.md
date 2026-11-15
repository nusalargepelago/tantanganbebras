# FORK.md — tantanganbebras

Fork dari **minimals** (upstream: branch `master`).
Aturan generik: **`docs/forking.md`** (master). Skeleton: `docs/FORK.template.md`.
File ini hanya berisi selisih yang spesifik fork ini.
Snapshot: 2026-11-15 · merge master `e31451d` — worktree master bersih,
tidak ada pekerjaan ter-commit tertunda di kedua sisi.

- Produk fork: platform lomba sekolah — event, practice, question bank,
  student import, todos, backup, "Tantangan Bebras". Spec: `docs/specs/`.
- Maintainer: muhamiyan.

## 2. Inventaris fork-owned (file baru — tidak konflik)

**Backend — domain baru** (pola 7-file master, register di `create_app.py`):
`app/dashboard/` (api/repositories/services), `app/event/` (+`api_student.py`),
`app/practice/`, `app/question/`, `app/student/` (+`api_auth.py`,
`api_dashboard.py`, `api_import.py`), `app/topic/`, `app/todos/`, `app/seed.py`,
`app/infra/backup.py`, `app/infra/{enums,naming,passwords,presenters,scoring,settings}.py`.

**Migrasi fork-owned** (setelah master `0001_initial.py`; jangan edit `0001`):
`app/migrations/versions/20261018_*.py` (6 file).

**Frontend — feature baru:**
`src/features/{backup,event,event-student,practice,question,student,todos}/`
lengkap, `features/dashboard/{store.ts, views/StudentDashboardView.vue,
views/TeacherDashboardView.vue}`, `src/app/tour/`, `src/app/focus-mode.ts`.

**Shared additions fork-owned:**
`shared/{labels.ts, richText.ts, questionOptions.ts, sanitize.ts, editorToolbar.ts,
editorUpload.ts}`,
`shared/components/{QuizRunnerShell.vue, CelebrationOverlay.vue}`,
`types/frappe-ui-editor.d.ts`, `docs/specs/*.md`, `docs/FEATURES.md`, `docs/PLAN.md`,
`tests/test_{backup,dashboard,event,practice,question,seed,student,todos,topic}.py`.
(`shared/composables/useCountdown.ts` ikut diserap ke master 2026-11-15 —
bilangannya masih ada di fork tapi isinya byte-identical dengan master.)

**Reusable — kandidat upstream** (lihat forking.md §7; jangan dipakai master
sebelum diserap):

| Item | Alasan | Status |
|---|---|---|
| `framework/infra/frontend.py`: `Cache-Control: no-cache` di HTML | Browser tidak cache shell (memuat CSRF token + SEO brand per request) | **diserap master 2026-11-15** — file fork = master byte-identical |
| `AppPageHeader.vue`: prop `title` (override breadcrumb/judul mobile) | Ekstensi aditif tanpa ubah kontrak | **diserap master 2026-11-15** — file fork = master byte-identical |
| `shared/labels.ts` (`categoryLabel`/`statusLabel`) | Enum→label i18n generik | kandidat |
| `shared/composables/useCountdown.ts` | Countdown kecil, reusable | **diserap master 2026-11-15** — file fork = master byte-identical |
| `shared/sanitize.ts` | HTML sanitizer untuk rich text (`v-html` question bank) | **fork-owned permanen — keputusan 2026-11-15:** bukan kandidat upstream; master tidak punya rich text (aturan dua konsumen §7.1) |
| `QuizRunnerShell.vue`, `CelebrationOverlay.vue` | Komponen fitur spesifik | fork-only |

## 3. Shared files dimodifikasi fork — tabel resolusi

Status per baris = hasil merge master `e31451d` (2026-11-15), 18 file konflik.

| File | Delta fork | Cara resolve |
|---|---|---|
| `frontend/src/app/navigation.ts` | nav lomba + `roles?: NavRole[]` | **Selesai:** interface **union** `roles?` + `requireAdmin?` (dua mekanisme hidup berdampingan); item `Users` = versi master (`lucide-users`, `requireAdmin: true`) |
| `.../UserSettingsDialog.vue` | tombol tour (`openCatalog`) | **Selesai:** skeleton master (brandStore, `languageOptions` dari i18n, BrandLogo); delta fork di-re-apply aditif |
| `.../AppShell.vue` | `focusMode`, `data-tour`, wrapper avatar | **Selesai:** skeleton master; **`BrandLogo size="fill"` menang** (fork masih `fill` polos — fix master `e31451d`); `v-if="!focusMode"` + `data-tour` re-apply |
| `.../menuStore.ts` | `NavRoleFlags` + filter berbasis `roles` | **Selesai:** `isAdmin` (master) dan `flags` (fork) keduanya dipakai; `visibleForRole` cek `requireAdmin` dulu, baru `roles` |
| `.../breadcrumbs.ts` | map breadcrumb fork | **Selesai:** fork = superset ketat, tidak ada kehilangan |
| `.../AppPageHeader.vue` | prop `title` | sudah byte-identical ke master (lihat §8) |
| `.../DashboardView.vue` | sector admin/teacher/student | **Selesai:** skeleton master (`AppPageHeader` + gate `auth.checked`) + sector fork → `AdminSchools/Teacher/StudentDashboardView`. `AdminDashboardView.vue` & `UserDashboardView.vue` tetap ada (versi master) tapi **tidak dirender** fork — dead code, disengaja |
| `.../AdminDashboardView.vue` | rewrite charts sekolah | tetap byte-identical; rewrite di `AdminSchoolsDashboardView.vue` (fork-owned) |
| `.../UsersView.vue` (add/add) | gate fork | **Selesai: master menang** — pakai `initialLoaded` + `gateReady` computed (fix master `0f6f9e0`) |
| `.../{RegisterView,LoginView}.vue`, `.../auth/{routes.ts,store.ts}` | panel/link fork | auto-merge + delta fork re-apply (`fetchClassification`) |
| `.../account/store.ts` | **`fetchUserTotal` dihapus** | jangan dihapus lagi (lihat §8) — sudah byte-identical ke master |
| `.../setup/store.ts` | BOM UTF-8 tak sengaja | tidak ikut konflik merge ini |
| `frontend/src/router/{guard,index,meta}.ts` | **di luar tabel lama** | **Selesai:** aditif — urutan guard auth **tidak** di-reorder; `requiresStaff`/`allowTeacher` + gate klasifikasi tetap; `children` routes fork = superset master (`accountRoutes` sudah termasuk) |
| `frontend/src/shared/composables/useListControls.ts` | tipe `fetch` | **Selesai: master menang** (`void \| Promise<unknown>` — superset dari `Promise<unknown>` fork) |
| `app/auth/repositories.py` | **di luar tabel lama** | **Selesai:** format master + delta fork di-re-apply — login tetap case-insensitive (`func.lower`) |
| `app/infra/roles.py` | **di luar tabel lama** | **Selesai:** skeleton master — `ensure_member_role()` dipertahankan persis master; delta fork jadi `ensure_builtin_roles()` (wrapper: seed `Member` + `Teacher`); `require_staff`/`require_student_manager`/`student_manager_scope` utuh; `__all__` = master + fungsi fork |
| `app/account/api.py` | `DELETE /users/<id>` | auto-merge; delta fork utuh (`@login_required` + `require_role("admin")` + `audit_log`) |
| `app/account/services.py` | ops user fork | auto-merge |
| `app/auth/models.py` | — | auto-merge (master hanya tambah docstring) |
| `app/create_app.py` | register blueprint/model fork | auto-merge; `ensure_builtin_roles()` tetap yang dipanggil |
| `app/infra/{seo,setup_dto}.py` | default brand fork | auto-merge; `setup_dto.py` tetap default fork |
| `framework/infra/config.py` | `MAX_CONTENT_LENGTH` → 64MB | tidak ikut konflik; tetap set di `.env` fork, bukan default master |
| `framework/infra/frontend.py` | `Cache-Control: no-cache` | byte-identical ke master `f89a413` |
| `frontend/src/app/locales/{en,id}.json` | kunci fork | **Selesai:** three-way merge per-key → **0 true conflict**; fork = superset ketat master (142 key fork-only, 0 master-only, 0 both-changed); parity en↔id terjaga |
| `.env.example` | var fork | tidak ikut konflik |
| `pyproject.toml` / `uv.lock` | dep fork | master **tidak** mengubah deps → `uv lock` tidak diperlukan merge ini |
| `CLAUDE.md` | section fork | **Selesai:** 6 konflik resolve ke fork (baris `DELETE /users/:id`, section onboarding/teacher, `BUILTIN_ROLES` `Member`+`Teacher`, daftar `features/`, `navigation.ts` role, urutan guard) — 0 konten master hilang |
| `README.md` | intro produk fork | **Selesai:** resolusi rerere lama dipertahankan (README terlokalisasi = intro fork + seluruh section operasional master); **`## Architecture` master yang hilang dikembalikan** |
| `tests/test_account.py` | `test_delete_user` | **Selesai:** test fork dipertahankan + test master masuk |
| `.claude/skills/*`, `index.html`, `index.css`, `brand.ts`, `.gitignore` | fork tweaks | auto-merge |

## 4. File yang fork hapus

| File | Aturan resolve |
|---|---|
| `frontend/src/features/dashboard/views/UserDashboardView.vue` | Master wins — file direstore; fork sembunyikan via route/nav |

## 5. Kontrak drift — update fork, jangan revert master

- `/api/v1/setup/status` publik → `{setupRequired, reason}`; detail engine/URL
  (mask) loopback-only. Fork: update `test_setup.py` / `test_contract.py` ke
  kontrak ini; di FE, `SetupStatus.activeEngine?`/`activeUrl?` opsional.
- `UserAdminOut` subclass `UserOut`; `require_owner_or_role` untuk
  `GET /account/users/:id`; pagination `distinct(User.id)` + bare-id — fork
  tidak perlu ubah apa pun.

## 6. Footguns fork ini

- `setup/store.ts` pernah terkontaminasi BOM — perhatikan saat konflik.
- `AdminDashboardView.vue` sudah bersih dari konflik sejak §8 selesai —
  perubahan tampilan admin sekolah dikerjakan di `AdminSchoolsDashboardView.vue`.
- Worktree harus bersih sebelum merge — WIP lama (`M app/auth/models.py`,
  `M .gitignore`) sudah di-commit/stash per 2026-11-15 (prep `f41b21b`).
  Cek `git status` dulu; kalau belum bersih → commit WIP > stash > jangan merge.
- Lockfile perlu `uv lock` ulang; fork tidak boleh hand-merge. (Merge
  `e31451d` tidak butuh — master tidak mengubah `pyproject.toml`/`uv.lock`.)
- Migrasi fork `0002+` bergantung pada skema master: setelah merge yang
  menyentuh `0001_initial.py`, jalankan fresh-boot check. Merge `e31451d`
  tidak menyentuh `0001` — fresh-boot tetap dijalankan, bersih.
- Endpoint fork (`/event`, `/practice`, …) tidak ada di CLAUDE.md table test
  master → `tests/test_docs.py` fork WAJIB punya baris fork; jangan matikan test.
- **rerere aktif** (`rerere.enabled=true`, cache di gitdir utama `rr-cache`,
  bukan worktree). Resolusi merge ini tercatat → konflik sama di merge
  berikutnya akan di-auto-resolve. Tetap wajib verify.
- **Jangan resolve konflik pakai `Set-Content` PowerShell 5.1** — menulis
  BOM UTF-8 + mojibake (`·` → `Â·`). Pakai
  `[System.IO.File]::ReadAllText/WriteAllText` dengan `UTF8Encoding($false)`
  dan join baris `"`r`n"` (working tree ini CRLF).

## 7. Security checklist tambahan fork

- Endpoint write fork: `@login_required` + gate (`require_role("admin")` dsb.)
  + `audit_log`. Termasuk `DELETE /users/<id>`.
- Student login/auth fork (`api_auth`) tetap ter-ratelimit; jangan bypass
  `RATE_LIMIT_AUTH`.
- Backup/restore: jangan aktif tanpa auth admin; `.env` backup tidak di-commit.

## 8. Re-align — SELESAI 2026-11-15 (semua sudah ter-commit)

Langkah yang dieksekusi:

1. `AdminDashboardView.vue` dipulihkan persis versi master (charts fork
   tidak lagi tinggal di file shared).
2. Rewrite fork dipindah ke `features/dashboard/views/AdminSchoolsDashboardView.vue`
   (file fork-owned, isi tidak berubah).
3. `DashboardView.vue` (fork) merender `AdminSchoolsDashboardView` untuk
   sektor admin — import satu-satunya yang berubah; perilaku produk sama.
4. `fetchUserTotal` dikembalikan ke `features/account/store.ts`
   (dibutuhkan `AdminDashboardView.vue` master; fork sengaja menghapusnya —
   itu penyebab kegagalan build/typecheck di master dashboard jika tidak
   dikembalikan).
5. Verifikasi: `yarn typecheck` ✓; `pytest` **480 passed** ✓.
   Build sengaja belum dijalankan.
6. 2026-11-15 (lanjutan): delta `AppPageHeader.vue` (prop `title` +
   fallback `breadcrumbMap` di judul mobile) diserap ke master; file fork
   disamakan byte-identical. `DashboardView.vue` di-align ke skeleton
   master (AppPageHeader + gate `auth.checked`) — masuk lewat `84e0bcc`
   lalu dikunci lagi oleh merge `ce3ad0e`.
   Verifikasi: `yarn typecheck` ✓; `yarn build` ✓ (52s).
   *(Rujukan `38bcbf8` di versi lama dokumen ini **dangling** — objek ada
   tapi tidak di branch mana pun; sha di atas adalah yang benar.)*

## 9. Riwayat merge & re-align

| Tanggal | Master sha | Konflik & resolve | Verifikasi |
|---|---|---|---|
| 2026-11-15 | `4c11655` | Bukan merge — re-align AdminDashboardView (lihat §8) | `typecheck` ✓; `pytest` 480 passed |
| 2026-11-15 | `498e808` | Bukan merge — `AppPageHeader.vue` byte-identical ke master (delta `title` diserap); `DashboardView.vue` di-align skeleton master | `typecheck` ✓; `build` ✓ |
| 2026-11-15 | `f89a413` | Bukan merge — `Cache-Control: no-cache` HTML diserap ke master; `framework/infra/frontend.py` file fork = master byte-identical; `sanitize.ts` ditetapkan fork-owned permanen | master `pytest` 243 passed; `ruff` ✓ |
| 2026-11-15 | `e31451d` | **Merge master → fork** (18 file konflik): resolve per tabel §3; `router/*` di luar tabel → aditif tanpa reorder guard; locale & `CLAUDE.md` = fork superset (0 konten master hilang); `UsersView.vue` master menang; `AppShell` ikut `size="fill"`; README: resolusi rerere dipertahankan + `## Architecture` master dikembalikan; `roles.py` = `ensure_member_role` (master) + `ensure_builtin_roles` (fork) | `pytest` **482 passed**; `ruff` ✓; `typecheck` ✓; `build` ✓ (56s); fresh-boot `flask db upgrade` `0001`→`20261114_9` ✓ |
