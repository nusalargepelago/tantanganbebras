# CLAUDE.md

Guidance untuk Claude saat bekerja di project **minimals**.

> **Project ini berbeda dari root repo `cells`.** `minimals` adalah Flask app
> **single-service** mandiri: punya `app/` + `framework/` sendiri, tidak ada
> `core/`, tidak ada `sdk/`, tidak ada entry-point discovery, tidak ada gateway.
> CLAUDE.md di root `cells/` tidak berlaku di sini — dokumen ini yang governs.

## Project Overview

**Minimals** — production-ready Flask app untuk cPanel/VPS di belakang Caddy,
dengan Vue 3 SPA (frappe-ui) yang di-serve oleh Flask sendiri.

| Path | Role |
|---|---|
| `framework/` | Shared, service-agnostic: base classes, API utils, exceptions, extensions, infra, logging, RBAC helpers |
| `app/` | Service ini: `auth` + `account` domain, `infra` cross-domain, migrations, config, entry point |
| `frontend/` | Vue 3 + Vite + Pinia + frappe-ui SPA. Build output → `app/static/frontend/` |
| `tests/` | pytest, 1 file per concern + `conftest.py` |
| `frappe-ui/` | Checkout sibling dari upstream (git-ignored, `.git` sendiri). **Bukan** dependency yang di-resolve build — `frontend/` ambil `frappe-ui@1.0.2` dari npm. Referensi baca saja. **Jangan diedit.** |

Single service, so: tidak ada `cells.services` discovery, tidak ada cross-service
SDK. Endpoint `/api/v1/app/*` adalah read API untuk service **luar** repo ini
(gated internal token / admin) — bukan untuk `core`.

## Commands

```bash
uv sync                        # install deps (single project)
uv run pytest                  # test suite
uv run ruff check .            # lint
uv run python -m app.run       # serve (waitress, default :8000)
uv run minimals                # sama — entry point script
uv run python -m app.cli setup # wizard via terminal (cPanel/headless)

# Frontend
cd frontend && yarn install && yarn dev     # Vite dev :5173, proxy /api → :8000
cd frontend && yarn build                   # → app/static/frontend/
cd frontend && yarn typecheck               # vue-tsc --noEmit

# Shortcut dari root
yarn serve / yarn dev / yarn build
```

Local HTTP dev wajib `FORCE_HTTPS=false`. Default **kode** `false`, tapi
`.env.example` ship `true` → loop redirect tanpa TLS proxy. Migration on boot:
`MIGRATE_ON_BOOT=true`.

## Architecture

### Domain-first layout

Tiap domain di `app/<domain>/`:

| File | Isi |
|---|---|
| `api.py` | HTTP saja: guard → validate DTO → delegate service → serialize presenter |
| `dto.py` | Pydantic input validation |
| `services.py` | Business logic + **transaction boundary** |
| `repositories.py` | Query & persistence — **tanpa** commit |
| `models.py` | SQLAlchemy model |
| `presenters.py` | Output serialization (camelCase) |
| `__init__.py` | Public surface — re-export `bp`, service, DTO, model, presenter |

Domain boleh punya `api_*.py` tambahan kalau butuh blueprint kedua di prefix
yang sama (`account/api_key_api.py` → `account_api_key_bp`). Semuanya tetap
sebagai `api` di layering.

`app/infra/` = cross-domain: health, CSRF, roles, audit, rate limit, security,
setup wizard, read API, API-key auth, db bootstrap.

Layered order — dependency hanya ke bawah:
`api → dto → services → repositories → models → presenters`

**Domain memanggil domain lain lewat repository yang di-inject ke service.**
`account` butuh user/role → lewat `AccountRepository` + `RoleRepository` yang
di-inject ke `AccountService`. Referensi: `app/account/services.py` constructor.

> **Known deviation:** aturan "service, bukan model" **belum sepenuhnya dipatuhi**.
> `app/account/services.py:7` masih `from app.auth.models import ... Role, User`
> (repository & presenter juga, `repositories.py:5`, `presenters.py:5`). Jangan
> tambah yang baru; kalau bisa, arahkan ke repository.

### Base classes (dari `framework/base`)

- **`DTOBase`** — `populate_by_name=True` (terima `fullName` **dan** `full_name`).
  `DTOBase.field(..., alias="fullName", min_length=8)`. **Tidak ada inferensi
  alias otomatis** — field snake_case tanpa `alias=` tetap snake_case di wire
  dan `fullName` dari client akan diabaikan (jatuh ke default). Tulis alias
  camelCase eksplisit di setiap field yang lewat API. `Cls.validate(
  request.get_json() or {})` → instance, atau `ValidationFailed` dengan key
  mis. `email_invalid_email`.
- **`PresenterBase`** — `from_model(obj, **overrides)` baca atribut via alias,
  coerce datetime → ISO-8601. `.to_dict()` default `by_alias=True` (camelCase).
  Tambahkan field presenter = menambah kontrak API (lihat §Wire format).
- **`ServiceBase[R]`** — wajib set `repository_class`. `_commit()` (catch
  `IntegrityError` → `Conflict("integrity_error")` + rollback), `_flush()`,
  `_rollback()`. **Semua commit terjadi di sini**, hanya di sini.
- **`RepositoryBase[T]`** — wajib set `model`. `get/find_one/find/list/count/
  add/delete/paginate`. **Transaction-agnostic — jangan pernah commit di sini.**

### Request lifecycle

```
:8000 → waitress → Caddy (TLS) → Flask
  /api/v1/*  → blueprint domain (CSRF dicek, kecuali yang di-exempt)
  /static/frontend/* → build asset SPA (cache 1 jam, filename content-hashed)
  /uploads/* → app/static/uploads (TANPA auth)
  /*        → SPA: file nyata bila ada, else index.html
              (brand + meta SEO di-inject server-side, lihat app/infra/seo.py)
  /robots.txt /sitemap.xml → crawler files (brand-driven, rate-limit exempt)
  /health /ready → health check
```

`register_spa()` dipanggil **setelah** semua blueprint, sebelum
`register_error_handlers()` — urutan ini wajib, catch-all tidak boleh shadow
rute API.

## Adding a Domain

1. `app/<domain>/` dengan 7 file di atas (`__init__.py`, `api.py`, `dto.py`,
   `models.py`, `presenters.py`, `repositories.py`, `services.py`).
2. `bp = BlueprintFactory("<name>", __name__, url_prefix="/api/v1/<name>")` di `api.py`.
3. **Import model di `app/create_app.py`** (blok `with app.app_context()`) —
   tanpa ini tabel tidak ikut `db.create_all()` / autodetect.
4. `app.register_blueprint(bp)` di `create_app.py`, **sebelum** `register_spa`.
5. **Tambah baris endpoint di tabel `## API Endpoints` dokumen ini** —
   `tests/test_docs.py` membandingkan tabel itu dengan `app.url_map`.
   Kalau lupa, test gagal.
6. Tambah test di `tests/test_<domain>.py`.

Tidak ada CLI generator di project ini (berbeda dengan root `cells`).

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user (public, rate-limited) |
| POST | /api/v1/auth/login | Login (public, rate-limited; any active account — staff & student, the role decides the menu) |
| POST | /api/v1/auth/logout | Logout (session) |
| GET | /api/v1/auth/me | Current user (session) |
| GET | /api/v1/auth/registration | Registration mode open/closed (public) |
| PUT | /api/v1/auth/registration | Set registration mode (admin) |
| GET | /api/v1/setup/status | First-run setup status (public) |
| POST | /api/v1/setup/db-test | Test DB connection (loopback client only) |
| POST | /api/v1/setup | Run first-run setup (loopback client only) |
| GET | /api/v1/csrf | Fetch CSRF token (public) |
| GET | /api/v1/account/users | List users (admin) |
| GET | /api/v1/account/users/:id | Fetch one user (owner or admin) |
| PATCH | /api/v1/account/users/:id | Update user (admin) |
| POST | /api/v1/account/users | Create user (admin) |
| DELETE | /api/v1/account/users/:id | Delete user (admin) |
| GET | /api/v1/account/roles | List roles (admin) |
| POST | /api/v1/account/roles | Create role (admin) |
| PATCH | /api/v1/account/roles/:id | Update role (admin) |
| DELETE | /api/v1/account/roles/:id | Delete role (admin) |
| POST | /api/v1/account/api-keys | Create API key (session) |
| GET | /api/v1/account/api-keys | List API keys (session) |
| DELETE | /api/v1/account/api-keys/:id | Revoke API key (session) |
| GET | /api/v1/topic | List topics (staff, paginated) |
| POST | /api/v1/topic | Create topic (staff) |
| GET | /api/v1/topic/:name | Fetch one topic (staff) |
| PATCH | /api/v1/topic/:name | Update topic (staff) |
| DELETE | /api/v1/topic/:name | Delete topic (staff) |
| POST | /api/v1/topic/reorder | Reorder topics (staff) |
| GET | /api/v1/question | List questions (staff, paginated) |
| POST | /api/v1/question | Create question (staff) |
| GET | /api/v1/question/option-list | Enum options for question filters (staff) |
| GET | /api/v1/question/:name | Fetch one question (staff) |
| PATCH | /api/v1/question/:name | Update question (staff) |
| DELETE | /api/v1/question/:name | Soft-delete question (staff) |
| POST | /api/v1/question/:name/restore | Restore question (staff) |
| DELETE | /api/v1/question/:name/purge | Purge question (staff) |
| GET | /api/v1/student/auth/login | Student login branding (public) |
| POST | /api/v1/student/auth/register | Student self-register (public, rate-limited) |
| POST | /api/v1/student/auth/login | Student login (public, rate-limited) |
| POST | /api/v1/student/auth/logout | Student logout (session) |
| GET | /api/v1/student/auth/me | Current student session |
| GET | /api/v1/student | List students (staff, paginated) |
| POST | /api/v1/student | Create student (staff) |
| GET | /api/v1/student/:userId | Fetch one student (staff) |
| PATCH | /api/v1/student/:userId | Update student (staff) |
| DELETE | /api/v1/student/:userId | Soft-delete student (staff) |
| POST | /api/v1/student/:userId/restore | Restore student (staff) |
| POST | /api/v1/student/:userId/activate | Activate student (staff) |
| DELETE | /api/v1/student/:userId/purge | Purge student (staff) |
| POST | /api/v1/student/import | Import students from XLSX (staff) |
| GET | /api/v1/student/import-template | Download XLSX import template (staff) |
| POST | /api/v1/student/practice/create | Create a 10-question practice sheet (student) |
| GET | /api/v1/student/practice/start | Resume the active practice (student) |
| POST | /api/v1/student/practice/answer-temp | Autosave one answer (student) |
| POST | /api/v1/student/practice/store | Submit & score a practice (student) |
| GET | /api/v1/student/practice/mine | List my practices (student) |
| GET | /api/v1/student/practice/:name | Practice result detail (owner) |
| GET | /api/v1/practice/:name | Practice review w/ shuffle (staff) |
| GET | /api/v1/practice | List all practices (staff, paginated) |
| GET | /api/v1/practice/settings | Practice settings — min questions (staff) |
| PUT | /api/v1/practice/settings | Update min questions (admin, audited) |
| GET | /api/v1/event | List events (staff, paginated) |
| POST | /api/v1/event | Create event (staff) |
| GET | /api/v1/event/:name | Fetch one event + questions (staff) |
| PATCH | /api/v1/event/:name | Update event (staff) |
| DELETE | /api/v1/event/:name | Soft-delete event (staff) |
| POST | /api/v1/event/:name/restore | Restore event (staff) |
| DELETE | /api/v1/event/:name/purge | Purge event (staff) |
| GET | /api/v1/event/:name/results | Event attempt results (staff) |
| GET | /api/v1/student/event | Candidate events for student |
| POST | /api/v1/student/event/make/:name | Start / resume an attempt (student) |
| GET | /api/v1/student/event/start/:name | Resume attempt runner (student) |
| POST | /api/v1/student/event/answer-temp | Autosave one answer (student) |
| POST | /api/v1/student/event/store | Submit & score an attempt (student) |
| GET | /api/v1/student/event/:name | Attempt result (owner) |
| GET | /api/v1/dashboard | Admin dashboard counters (staff) |
| GET | /api/v1/dashboard/stats | Admin dashboard statistics — schools, registrations, categories (staff) |
| GET | /api/v1/student/dashboard | Student dashboard (student) |
| GET | /api/v1/todos | List todos (paginated) |
| POST | /api/v1/todos | Create todo (session) |
| GET | /api/v1/todos/:id | Fetch one todo (owner or admin) |
| PATCH | /api/v1/todos/:id | Update todo (owner or admin) |
| PUT | /api/v1/todos/:id | Update todo (owner or admin) |
| DELETE | /api/v1/todos/:id | Delete todo (owner or admin) |
| GET | /api/v1/account/menu-preferences | Menu order/visibility (session) |
| PUT | /api/v1/account/menu-preferences | Save menu order/visibility (session) |
| GET | /api/v1/app/ping | Liveness of the read API (public) |
| GET | /api/v1/app/users | Cross-service read API (internal token or admin) |
| GET | /api/v1/app/roles | Cross-service read API (internal token or admin) |
| POST | /api/v1/uploads | Upload image (admin, max 5 MiB, png/jpg/jpeg/webp/gif) |
| DELETE | /api/v1/uploads/:name | Delete uploaded image (admin, idempotent 204) |
| GET | /api/v1/backup/export | Download full SQL backup (admin, audited) |
| POST | /api/v1/backup/import | Restore SQL backup, overwrite (admin, 2/min, audited) |
| GET | /robots.txt | Crawler instructions, brand-driven (public) |
| GET | /sitemap.xml | Canonical site URL for crawlers (public) |
| GET | /health | Health check (public) |
| GET | /ready | Readiness check (public) |

## Wire format (kontrak — diuji `tests/test_contract.py`)

Tidak ada `{"data": ...}` envelope.

| Kasus | Bentuk |
|---|---|
| Single / mutasi sukses | objek telanjang, `200`/`201` |
| List | `{"items": [...]}` |
| Paginated | `{"items", "total", "page", "perPage"}` (`perPage` camelCase) |
| No content | `204`, body kosong |
| Error | `{"message": "<snake_case_key>"}` |

- Response **selalu camelCase**. DTO/presenter enforce lewat alias.
- Error key **selalu snake_case** lowercase (`role_not_found`). Setup wizard
  juga mengikuti aturan ini: `db_bootstrap.db_error_key()` memetakan exception
  driver ke key (`invalid_db_credentials`, `db_unreachable`, `db_not_found`,
  `db_timeout`, `unknown_db_host`, `db_connection_failed`). Detail host/port
  tetap di log server, tidak bocor ke response.
- FE humanisasi via `getErrorMessage()`: `not_found` → `Not found`.

## Error contract

`framework/exceptions` — semua membawa HTTP status, dipetakan otomatis oleh
`register_domain_handlers()`:

| Exception | Status | Pakai untuk |
|---|---|---|
| `NotFound` | 404 | resource tidak ada |
| `Unauthorized` | 401 | butuh auth |
| `Forbidden` | 403 | auth ok, akses ditolak |
| `ValidationFailed` | 400 | input tidak valid |
| `Conflict` | 409 | duplikat / race |
| `InvalidOperation` | 422 | aturan bisnis dilanggar |

`DomainException` base = 400. `ValueError` **tidak** di-handle → jadi 500
(sengaja: itu programming error, bukan client error).

Handler inherited (400/401/403/404/405/413/422/429/500 + `CSRFError`) punya key
tetap. **Service raise exception, bukan return response.** Layer
tanggung jawab: DTO (shape) → Service (business) → API (auth + HTTP status).

## Auth & Authorization

Dua mekanisme, keduanya menghasilkan `current_user`:

1. **Session** — Flask-Login. `@login_required`.
2. **API key** — header `X-API-Key: sk-...`, dicek di `before_request`
   (`app/infra/api_key_auth.py`), lalu `login_user(..., force=True)`. Key
   disimpan **bcrypt-hashed** + `prefix` 10 char untuk lookup; raw key hanya
   muncul sekali di respons create.

**Registration gate** — `POST /api/v1/auth/register` bisa ditutup lewat
`PUT /api/v1/auth/registration` (admin, `require_role("admin")`). Mode
`open`/`closed` disimpan di tabel `settings` (`registrationMode`, default
`open`, fail-safe di `app/infra/registration.py`); saat `closed` register
ditolak 403 `registration_disabled` + audit `register_failure`. `GET
/api/v1/auth/registration` publik — dipakai FE untuk menyembunyikan link
"Create one" dan me-redirect `/register` ke `/login`.

Dua konsep role, jangan dicampur:

- **`User.app_role`** — kolom string, nilainya `"user"` atau `"admin"`. Ini yang
  dicek `require_role("admin")`. Sangat sederhana, hard-coded.
- **`Role` + `user_roles`** — tabel role relasional (seeded `Member`).
  Untuk display/label dan FUTURE permission granularity.

`require_role(*roles)` / `require_owner_or_role(owner_id, *roles)` dari
`framework.auth` — return `None` kalau boleh, atau response tuple yang langsung
di-`return` dari view:

```python
if denied := require_role("admin"):
    return denied
```

## CSRF

- Aktif `CSRF_ENABLED` (default true). Token dari `GET /api/v1/csrf`.
- Blueprint **di-exempt**: `app_api`, `csrf`, `health`. Daftarkan di
  `create_app._init_csrf()`.
- Setelah login/register: `clear_session_keep_csrf()` — session di-clear tapi
  token CSRF dipertahankan, supaya token tidak invalid setelah login.
- FE: interceptor axios otomatis ambil + kirim `X-CSRFToken` untuk
  POST/PUT/PATCH/DELETE, dengan retry sekali kalau ditolak.

## Migrations

- **Satu** direktori Alembic: `app/migrations/`. Single service — tidak pernah
  `flask db` dari tempat lain.
- `MIGRATE_ON_BOOT=true` → `upgrade()` jalan sebelum server start.
- Command manual: `uv run flask --app app.create_app:create_app db upgrade`
- **Alpha: fix di titik masalah, jangan numpuk history.** Schema salah →
  edit `0001_initial.py` langsung, bukan tambah revision baru. Hanya tambah
  revision kalau user minta.
- Index di `0001_initial.py` harus **selaras dengan `index=True` di model** —
  test path (`db.create_all()`) dan production path (`flask db upgrade`)
  harus menghasilkan skema identik. Kalau model berubah, index di migrasi
  ikut berubah.
- Setup wizard menjalankan `migrate_to(url, MIGRATIONS_DIR)` dengan engine
  sendiri (`target_metadata = None`, autogenerate tidak dipakai) —migration
  harus eksplisit.

## Config

`.env` di root project. `BaseConfig` (`framework/infra/config.py`) membaca
semua; `app/config.py` menambah path & static.

| Var | Default | Notes |
|---|---|---|
| `SECRET_KEY` | — | **Wajib**, ≥32 chars, bukan placeholder (dicek, raise saat import) |
| `DATABASE_URL` | `sqlite:///app.db` | Path relatif → `data/`. sqlite / mysql+pymysql / postgresql+psycopg |
| `FLASK_DEBUG` | `false` | `true` → dev server, bukan waitress |
| `PORT` | `8000` | Bind port waitress; juga jadi akhiran nama cookie sesi |
| `SESSION_COOKIE_NAME` | `session_{PORT}` | Cookie sesi. Cookie browser disimpan per host, bukan per port — akhiran `PORT` yang memisahkan dua instance di satu mesin; replika satu deployment (PORT sama) tetap berbagi |
| `REMEMBER_COOKIE_NAME` | `remember_{PORT}` | Sama, untuk remember-me |
| `FORCE_HTTPS` | `false` | Cookie secure, HSTS, SameSite=None |
| `TRUSTED_PROXY` | `false` | Lihat §Security |
| `CSRF_ENABLED` | `true` | |
| `CORS_ORIGINS` | — | CSV. Kosong = CORS mati, SameSite=Lax |
| `RATE_LIMIT_DEFAULT` | `200/hour` | Route API saja |
| `RATE_LIMIT_AUTH` | `10/minute` | Login & register |
| `RATE_LIMIT_STORAGE_URL` | — | Kosong = in-memory (single worker) |
| `TALISMAN_ENABLED` | ikut `FORCE_HTTPS` | CSP + HSTS + secure headers |
| `TALISMAN_CSP` | `DEFAULT_CSP` di `framework/extensions/talisman.py:6` | Dikosongkan = pakai default. **Jangan** diisi string kosong agar CSP mati — `init_talisman` jatuh ke `DEFAULT_CSP` |
| `LOG_LEVEL` / `LOG_FILE` | `INFO` / `data/app.log` | Default di `app/config.py:46`. `data/` = satu-satunya path writable di container. File handler = rotating 10MB × 5 |
| `ALERT_WEBHOOK_URL` | — | Alert record → webhook (async, queue) |
| `INTERNAL_API_TOKEN` | — | Gate `/api/v1/app/*` untuk non-browser client |
| `MIGRATE_ON_BOOT` | `false` | |
| `SEO_INDEXABLE` | `true` | `false` → `noindex, nofollow` + `robots.txt` disallow |
| `APP_LANG` | `en` | Fallback `appLang` (pilihan bahasa setup → `settings.appLang`); atribut `lang` + tag SEO. Preferensi pengunjung = cookie `minimals-lang` |
| `SQLALCHEMY_POOL_*` | 10/20/30/1800 | **Diabaikan untuk sqlite** |

## Security model

- **Proxy trust bersifat ganda.** `TRUSTED_PROXY=true` saja tidak cukup —
  rewrite `X-Forwarded-*` hanya dipakai kalau socket peer juga
  private/loopback. Header dari peer publik tidak pernah dipercaya, walau flag
  aktif. `RAW_REMOTE_ADDR` disimpan sebelum ProxyFix untuk ini.
- **Setup wizard hanya loopback.** `POST /api/v1/setup*` menolak kecuali
  raw socket peer **dan** effective address **dan** `X-Forwarded-For` terakhir
  semuanya loopback — klien private network (sesama VM di VPC) ditolak.
  SQL-injection ke cloud metadata juga dicek
  (`_deny_metadata_host` menolak link-local).
- **Rate limit** di-key per IP efektif; exempt: SPA asset/route, `/uploads/*`,
  `/health`, `/ready`.
- **Audit trail** — `audit_log(action, user_id=, resource=, details=)` pada
  setiap write penting (register, login, logout, update user/role). Nunca
  gagalkan operasi bisnis kalau audit gagal.
- **Password** — `werkzeug.security.generate_password_hash`, default **scrypt**
  (`scrypt:32768:8:1`). Policy: min 8, upper + lower + digit + special.
- **API key** — **bcrypt** hash (`app/account/models.py`), prefix 10 char untuk
  lookup, raw key hanya muncul sekali di respons create, `masked_name` di list.

## Frontend

Vue 3 + Vite + Pinia + frappe-ui (`1.0.2`), TypeScript strict.

```
src/
  app/       AppShell, i18n.ts + locales/{en,id}.json, useMediaQuery — shell, i18n & layout
  features/  <feature>/{routes.ts, store.ts, views/*.vue} — auth, setup, dashboard
  shared/    api/{client.ts, errors.ts, index.ts} — SATU-SATUNYA axios instance
  router/    index.ts + guard.ts + meta.d.ts
```

- **Selalu** `import { api } from '@/shared/api'` dengan route tanpa prefix
  (`baseURL: '/api/v1'` sudah handles). **Jangan** `axios.create()` baru,
  **jangan** `fetch()`, **jangan** set header CSRF manual.
- **Jangan pakai data-layer frappe-ui** — `useCall`, `useList`, `createResource`,
  `useFetch` mengasumsikan backend Frappe. Repo ini Flask. Skill upstream
  misleading di bagian itu.
- **Error handling di store**: `error.value = getErrorMessage(e, fallback)` —
  FE humanisasi snake_case jadi sentence. Return `null`/`false` agar view tahu
  gagal; `toast` **setelah** await selesai. `error.<key>` ada di locale →
  pesan backend ikut bahasa; fallback store pakai `i18n.global.t(...)`.
- **i18n**: `vue-i18n` legacy:false — `app/i18n.ts` + `app/locales/{en,id}.json`
  (key **wajib identik** antar locale). Resolusi locale: localStorage
  `minimals-lang` → cookie → `window.appLang` (hasil setup wizard) → `en`.
  Ganti teks view = ubah `t('key')` + **kedua** locale; label password rule =
  key (`auth.passwordRules.*`) di `validation.ts`, crumb = key (`crumb.*`).
  Switcher bahasa: dialog **Settings → Preferences** (`app/UserSettingsDialog.vue`);
  tema: tab bar `app/ThemeSwitcher.vue` — di menu avatar (desktop) dan baris
  Tema di Preferences. Wizard setup punya select bahasa di langkah Brand
  (disimpan ke `settings.appLang`).
- **Router guard urutan**: setup dulu (`setupRequired` → semua nav ke `/setup`),
  baru auth (`requiresAuth` / `guestOnly`). `setupRequired` = schema atau
  user kosong.
- **Per-page `<head>`**: `router.afterEach` (`router/index.ts`) mengisi
  `document.title`/`meta description` dari kunci i18n `route.<Name>.title`
  dan `route.<Name>.description` (fallback `meta.title`/`meta.description`
  di `routes.ts`, lalu brand description; tag dihapus kalau keduanya kosong).
  Di-resolve ulang saat locale berganti. Halaman baru = tambah kunci
  `route.<Name>.*` di **kedua** locale.
- **401 global**: interceptor fire event `auth:unauthorized` → router
  redirect. **Jangan** tangani 401 per-request.
- **Ikon**: `lucide-*` (string, via unplugin-icons). Shape:
  `<span class="lucide-log-in size-6" aria-hidden="true" />` atau
  `:icon-left="'lucide-log-in'"`.
- **Styling**: Tailwind + token frappe-ui v1 (`text-2xl-semibold`,
  `text-p-sm`, `rounded-6`, `bg-surface-elevation-2`, `text-ink-gray-8`).
  Jangan pakai palet Tailwind mentah untuk surface/ink.

> **Skills di `.claude/skills/`** — `wiring` (bridges frontend↔Flask: axios
> client, Pinia, CSRF, auth flow), `polish` (cosmetics/presentasi), `review`
> (review & fix workflow atas git working tree), dan `translate` (kanon i18n
> EN/ID: locale key, error dictionary, bahasa setup/boot) semuanya memakai
> path yang cocok dengan project ini. Kalau skill dan `frontend/src/`/`app/`
> bertentangan, **kode yang menang**.

## Tests

```bash
uv run pytest
uv run pytest tests/test_auth.py -q
```

Fixture di `tests/conftest.py`: `app`, `client` (CSRF-ready), `member`, `admin`.
`csrf_client(app)` ambil token dulu lalu set `HTTP_X_CSRFTOKEN`. Test DB = sqlite
di temp dir, dibuat via `db.create_all()`.

`tests/test_docs.py` menjaga agar **tabel endpoint dan `url_map` sinkron** —
tambah endpoint wajib tambah baris di tabel `## API Endpoints` dokumen ini.
Ini gotcha paling sering terlewat.

## Pitfalls

1. **Daftar endpoint baru = tambah baris di tabel `## API Endpoints`**,
   atau `test_docs.py` gagal.
2. **Presenter baru = kontrak API berubah.** Menambah field ke presenter yang
   sudah ada itu breaking — tambah endpoint baru atau presenter terpisah,
   jangan ganggu yang lama.
3. **Tambah kolom model = tambah kolom di `0001_initial.py`** (alpha, single
   migration), bukan revision baru.
4. **Model harus di-import di `create_app.py`** agar terdaftar di metadata.
5. **Blueprint harus didaftarkan sebelum `register_spa`** — catch-all akan
   menshadow.
6. **Blueprint baru yang kena CSRF** — exempt di `_init_csrf()` kalau memang
   non-browser (API key, health, read API).
7. **`index.html` dirender lewat Jinja** (`_render_index_html`) untuk inject
   `{% for key in boot %}`. Sintaks `{{ }}` / `{% %}` literal di `index.html`
   akan ikut dieksekusi Jinja — jangan tulis raw.
8. **Commit hanya di service.** `db.session.commit()` di repository atau
   `api.py` = pelanggaran boundary; `IntegrityError` tidak akan caught.
   Logout auth sudah lewat `AuthService.record_logout()`.
9. **`FORCE_HTTPS=true` tanpa TLS proxy = loop redirect.** Set `false` untuk
   local HTTP.
10. **`data/` dan `app/static/frontend/` git-ignored** — hasil runtime/build,
    jangan di-commit. `LOG_FILE` default mengarah ke `data/app.log` agar
    container non-root tetap bisa menulis.
11. **Relative sqlite path** di-resolve ke `data/` (volume-friendly di Docker).
    Ganti engine lewat `DATABASE_URL`, bukan hardcode.
12. **UUID = UUIDv7** (`framework.infra.uuid7`) — time-ordered, bukan `uuid4`.
    Primary key selalu `String(36)` + `default=_uuid`.
13. **Migrasi on boot jalan di dalam `create_app()`**, sebelum
    `ensure_member_role()` — jangan panggil `run_migrations()` lagi di
    `run.py`, dan jangan seed sebelum migrasi.
14. **Brand/SEO** — `<title>`, meta description, robots, canonical, OG di
    `index.html` di-inject server-side (`app/infra/seo.py` →
    `_apply_seo`); sumber kebenaran = tabel `settings`. `<title>` di
    `frontend/index.html` hanya fallback dev. SPA membaca
    `window.brand`; `seo` tidak pernah jadi window global.

## Deployment

`Dockerfile` (python:3.11-slim, non-root `appuser`, `/app/data` volume) +
`docker-compose.yml` (bind `127.0.0.1:8000`, `MIGRATE_ON_BOOT=true`) +
`Caddyfile` (TLS + reverse proxy). Setup: build FE → `.env` dengan `SECRET_KEY`
nyata → Caddy → `TRUSTED_PROXY=true` di belakang proxy.

Known gaps ada di README § *Security notes* (`/uploads/*` tanpa auth,
`/register` terbuka, status endpoint publik). Baca sebelum eksposur internet.
