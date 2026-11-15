# FORK.md — tantanganbebras

Fork dari **minimals** (upstream: branch `master`).
Aturan generik: **`docs/forking.md`** (master). Skeleton: `docs/FORK.template.md`.
File ini hanya berisi selisih yang spesifik fork ini.
Snapshot: 2026-11-15 · master `fba5c658` + cleanup working tree (uncommitted).

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

| File | Delta fork | Cara resolve |
|---|---|---|
| `frontend/src/app/navigation.ts` | nav lomba (+~73 baris) | Master skeleton; spread item fork di bawah item master |
| `.../UserSettingsDialog.vue` | panel fork | Master skeleton; blok fork sebagai section baru |
| `.../AppShell.vue` | shell tweaks | Master skeleton; re-apply |
| `.../menuStore.ts` | preferensi fork | Master logic; field fork aditif |
| `.../breadcrumbs.ts` | map breadcrumb fork | Union map |
| `.../AppPageHeader.vue` | prop `title` | **Selesai 2026-11-15:** diserap master; file fork disamakan byte-identical — tidak ada delta fork |
| `.../DashboardView.vue` | tweak fork | Master wins; re-apply |
| `.../AdminDashboardView.vue` | rewrite (charts sekolah) | **Selesai 2026-11-15:** file = master persis; rewrite di `AdminSchoolsDashboardView.vue` (fork-owned); `DashboardView.vue` import fork view |
| `.../{UsersView,RegisterView,LoginView}.vue`, `.../auth/{routes.ts,store.ts}` | panel/link fork | Master skeleton; re-apply aditif |
| `.../account/store.ts` | **`fetchUserTotal` dihapus** | **Selesai 2026-11-15:** `fetchUserTotal` dikembalikan (dibutuhkan dashboard master). Penghapusan adalah penyebab regresi build di dashboard master — jangan dihapus lagi |
| `.../setup/store.ts` | BOM UTF-8 tak sengaja | Buang BOM; master wins |
| `app/account/api.py` | `DELETE /users/<id>` | Master skeleton; re-apply aditif + `@login_required` + `require_role("admin")` + `audit_log` |
| `app/account/services.py` | ops user fork | Master skeleton; re-apply |
| `app/auth/models.py` (worktree, belum ter-commit) | kolom/relasi fork | Master skeleton; kolom fork aditif + cek fork-migration nyambung |
| `app/create_app.py` | register blueprint/model fork | Master skeleton; blok fork terpisah, sebelum `register_spa` |
| `app/infra/{roles.py, seo.py, setup_dto.py}` | default brand fork | Master wins struktur; `setup_dto.py` boleh pertahankan default **fork** |
| `framework/infra/config.py` | `MAX_CONTENT_LENGTH` → 64MB (restore backup) | Lebih baik set di `.env` fork; kembalikan default master |
| `framework/infra/frontend.py` | `Cache-Control: no-cache` | **Selesai 2026-11-15:** diserap master; file fork = master byte-identical |
| `locales/{en,id}.json` | kunci fork | Aditif + parity en↔id wajib |
| `.env.example` | var fork | Aditif |
| `pyproject.toml` / `uv.lock` | dep fork | `uv lock` ulang, jangan hand-merge |
| `CLAUDE.md` / `README.md` | section fork | Master otoritatif; fork append section; tabel endpoint fork → `test_docs.py` hijau |
| `.claude/skills/*`, `index.html`, `index.css`, `brand.ts`, `.gitignore` | fork tweaks | Master wins kecuali konflik nyata |

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
- Worktree berisi WIP (`M app/auth/models.py`, `M .gitignore`, dll.) yang
  belum ter-commit — commit/stash dulu sebelum merge.
- Lockfile perlu `uv lock` ulang; fork tidak boleh hand-merge.
- Migrasi fork `0002+` bergantung pada skema master: setelah merge yang
  menyentuh `0001_initial.py`, jalankan fresh-boot check.
- Endpoint fork (`/event`, `/practice`, …) tidak ada di CLAUDE.md table test
  master → `tests/test_docs.py` fork WAJIB punya baris fork; jangan matikan test.

## 7. Security checklist tambahan fork

- Endpoint write fork: `@login_required` + gate (`require_role("admin")` dsb.)
  + `audit_log`. Termasuk `DELETE /users/<id>`.
- Student login/auth fork (`api_auth`) tetap ter-ratelimit; jangan bypass
  `RATE_LIMIT_AUTH`.
- Backup/restore: jangan aktif tanpa auth admin; `.env` backup tidak di-commit.

## 8. Re-align — SELESAI 2026-11-15 (sebagian menunggu commit)

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
   master (AppPageHeader + gate `auth.checked`), commit `38bcbf8`.
   Verifikasi: `yarn typecheck` ✓; `yarn build` ✓ (52s).

## 9. Riwayat merge & re-align

| Tanggal | Master sha | Konflik & resolve | Verifikasi |
|---|---|---|---|
| 2026-11-15 | `4c11655` | Bukan merge — re-align AdminDashboardView (lihat §8) | `typecheck` ✓; `pytest` 480 passed |
| 2026-11-15 | master worktree (uncommitted) | Bukan merge — `AppPageHeader.vue` byte-identical ke master (delta `title` diserap); `DashboardView.vue` di-align skeleton master | `typecheck` ✓; `build` ✓ |
| 2026-11-15 | master (uncommitted) | Bukan merge — `Cache-Control: no-cache` HTML diserap ke master; `framework/infra/frontend.py` file fork = master byte-identical; `sanitize.ts` ditetapkan fork-owned permanen | master `pytest` 243 passed; `ruff` ✓ |
