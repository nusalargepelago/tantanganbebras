# Minimals

Untuk tim kecil dengan cPanel/VPS seadanya: satu service, satu database, satu
container di belakang Caddy. Tanpa gateway, tanpa microservice, tanpa platform
tambahan — clone, isi `SECRET_KEY`, jalankan wizard, selesai. "Minimals"
hanyalah default; di production, brand-nya milikmu.

**Status: open alpha** — dipakai sungguhan, tapi skema & kontrak masih bisa
berubah; kompatibilitas antar versi belum dijanjikan.

| | |
|---|---|
| **Backend** | Flask 3 · SQLAlchemy 2 · Pydantic 2 · Flask-Login · Alembic · waitress |
| **Frontend** | Vue 3 · Vite · Pinia · frappe-ui · Tailwind (TS strict) |
| **Database** | SQLite · MariaDB/MySQL · PostgreSQL |
| **Deploy** | Docker (non-root) + Caddy (TLS) · cPanel/Passenger |

## Highlights

- **White-label & SEO** — brand (nama, tagline, deskripsi, site URL, bahasa)
  diatur sekali di wizard; logo diganti admin dari Pengaturan. Semuanya
  di-inject server-side ke `<title>`/meta/robots/Open Graph, plus label SPA &
  judul/meta description per halaman. Default seluruh stack "Minimals".
- **Auth lengkap** — session + API key, role admin/member, dan **registration
  gate**: admin bisa menutup/membuka pendaftaran lewat API, efektif tanpa
  restart, untuk deployment invite-only.
- **First-run wizard** — pilih database (SQLite/MySQL/PostgreSQL), tes
  koneksi, brand, lalu buat administrator. Hanya menerima klien loopback.
- **Keamanan aktif by default** — CSRF, rate limit, CSP/HSTS, audit log,
  password scrypt.
- **SPA Vue 3 di-serve Flask** — tanpa web server terpisah untuk frontend;
  Docker image non-root.

## Quick Start

```bash
uv sync
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # → SECRET_KEY
```

`SECRET_KEY` wajib ≥32 karakter; placeholder ditolak dan app refuse boot.
SQLite default ada di `data/app.db` (git-ignored).

```bash
uv run python -m app.run                        # waitress di :8000
MIGRATE_ON_BOOT=true uv run python -m app.run    # migration dulu
```

Dev lokal via HTTP biasa: set `FORCE_HTTPS=false` — default `.env.example`
`true`, dan tanpa TLS proxy akan loop redirect.

## First-run Setup

Sampai setup selesai, SPA mengarahkan semua navigasi ke `/setup`. Wizard
(loopback-only — buka dari server atau SSH tunnel
`ssh -L 8000:localhost:8000 server` → `http://127.0.0.1:8000/setup`) menulis
`DATABASE_URL` ke `.env`, memigrasi target, membuat admin, dan menyimpan brand
+ bahasa. Kalau database target beda dari engine aktif, respons meminta
restart.

## White-label & SEO

Brand disimpan di tabel `settings` dan di-inject server-side tiap request
`index.html` — crawler tidak perlu menjalankan JS. `robots.txt` dan
`sitemap.xml` mengikuti brand; canonical/`og:url` hanya muncul setelah **Site
URL** diisi (tidak pernah dari header `Host`).

- Env: `SEO_INDEXABLE=false` → `noindex` + robots disallow; `APP_LANG` →
  fallback bahasa (`en` default). Preferensi pengunjung di cookie
  `minimals-lang`.
- Logo (admin saja) diunggah dari **Pengaturan → Aplikasi → Brand**; dipakai
  di sidebar, halaman masuk, favicon, dan `og:image` (saat Site URL diisi).
  Sebelum diunggah, logo dipotong persegi di klien (geser + zoom, output PNG
  ≤512px). Hanya URL `/uploads/*` hasil upload aplikasi yang diterima, dan file
  lama dihapus saat logo diganti atau dikosongkan.
- DB lama yang dibuat **sebelum** fitur ini tidak otomatis punya tabel
  `settings` — recreate DB, atau buat manual
  (`id CHAR(36) PK, key VARCHAR(64) UNIQUE, value TEXT DEFAULT ''`).

## Development

```bash
uv run pytest
uv run ruff check .

cd frontend && yarn install
yarn dev                     # Vite :5173, proxy /api → :8000
yarn build                   # → app/static/frontend/
yarn typecheck
```

## Production (cPanel/VPS + Caddy)

1. `cd frontend && yarn install && yarn build`
2. `.env` dengan `SECRET_KEY` asli + `DATABASE_URL`
3. Arahkan Caddy (`Caddyfile`) ke `localhost:8000`
4. `TRUSTED_PROXY=true` (hanya di belakang proxy) — `FORCE_HTTPS=true`
   (default) asalkan Caddy kirim `X-Forwarded-Proto`
5. `uv run python -m app.run`

Shared hosting cPanel (Passenger, tanpa container) punya jalur sendiri — lihat
[`docs/deploy-cpanel.md`](docs/deploy-cpanel.md).

## Docker

```bash
docker compose up --build
```

Bind `127.0.0.1:8000` (Caddy di depan), `MIGRATE_ON_BOOT=true` sudah
diset. Kalau SQLite dipakai dan host volume `./data` tak writable oleh
container, jalankan `sudo chown -R 10001:10001 data` (uid `appuser`).
Database dari dalam container tidak persist — set `DATABASE_URL` di `.env`.

## Architecture

Satu service dengan domain berlapis (`api → dto → services → repositories →
models → presenters`); commit hanya di service; response camelCase, error
`{"message": "<snake_case_key>"}`. Detail & konvensi lengkap:
[`CLAUDE.md`](CLAUDE.md), [`framework/README.md`](framework/README.md).

## Security notes

Baca sebelum eksposur internet:

- `/uploads/*` diserve **tanpa autentikasi** — jangan simpan file sensitif di
  `app/static/uploads/`
- `POST /api/v1/auth/register` terbuka (mode default `open`) dan langsung
  login. Tutup via `PUT /api/v1/auth/registration` (admin) untuk deployment
  invite-only
- `/api/v1/setup/status` dan `/health` publik. Status setup hanya mengekspos
  `setupRequired` + `reason` (bocoran terbatas: instance belum dikonfigurasi);
  detail engine/URL database ter-mask hanya untuk klien loopback. `/health`
  mengekspos metrik agregat
- API key hanya mengautentikasi request read; mutasi tetap butuh CSRF session
- Rate limit per IP efektif, hanya route API; set `RATE_LIMIT_STORAGE_URL`
  (mis. `redis://…`) untuk multi-worker
- `TRUSTED_PROXY=true` hanya di belakang proxy: rewrite `X-Forwarded-*` cuma
  dipercaya dari peer private/loopback

## Contributing

Selama open alpha, kontribusi hanya untuk **perbaikan bug** — issue maupun PR
fix diterima. Fitur baru tidak diterima.

## License

[MIT](LICENSE) — © 2026 Apriliansyah Idris.
