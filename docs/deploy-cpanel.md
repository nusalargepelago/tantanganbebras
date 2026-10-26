# Deploy ke cPanel

Runbook untuk men-deploy Minimals ke shared hosting cPanel yang punya menu
**Setup Python App** (Phusion Passenger). Ini jalur alternatif dari
`Dockerfile`/`Caddyfile` — di cPanel tidak ada container, tidak ada TLS
proxy sendiri, dan **tidak ada waitress**: Passenger yang meng-import WSGI
callable dari `passenger_wsgi.py`.

> `uv run python -m app.run` **tidak berlaku di sini.** Entry point waitress
> hanya untuk lokal/VPS. Di cPanel, `app/run.py` tidak pernah dipanggil.

## Prasyarat

| Kebutuhan | Detail |
|---|---|
| Python | **3.11+** (`requires-python`). Pilih 3.11/3.12 di Setup Python App. |
| Akses | SSH atau menu **Terminal** di cPanel. Wajib — wizard setup hanya bisa dari CLI. |
| Database | MariaDB/MySQL + user + database dari menu **MySQL® Databases**. |
| Domain | Domain/subdomain yang mengarah ke hosting ini. |

## 1. Build frontend (di mesin lokal)

`app/static/frontend/` **git-ignored** dan tidak ada di repo. Tanpa folder ini
SPA hanya membalas "frontend not built" (semua rute non-API tetap 404 HTML).

```bash
yarn build        # → app/static/frontend/ (index.html + assets/)
```

## 2. Upload

Upload ke Application root (mis. `/home/USER/minimals`):

```
app/                 framework/           passenger_wsgi.py
pyproject.toml       requirements.txt
app/static/frontend/                     ← hasil build, jangan lupa
```

Yang **tidak** di-upload: `.venv/`, `data/`, `node_modules/`, `frontend/`,
`frappe-ui/`, `.git/`, `.env` (dibuat di server).

Alternatif: **Git™ Version Control** di cPanel untuk clone repo, lalu upload
folder `app/static/frontend/` secara terpisah — folder itu tidak ikut ter-clone.

## 3. Setup Python App

cPanel → **Setup Python App** → **Create Application**:

| Field | Isi |
|---|---|
| Python version | 3.11 atau 3.12 |
| Application root | `minimals` |
| Application URL | domain/subdomain kamu |
| Application startup file | **kosong** |
| Application entry point | **kosong** |

Setelah dibuat, cPanel menampilkan command aktivasi venv — copy persis dari UI,
bentuknya:

```bash
source /home/USER/virtualenv/minimals/3.11/bin/activate && cd /home/USER/minimals
```

## 4. Install dependensi

```bash
source /home/USER/virtualenv/minimals/3.11/bin/activate && cd /home/USER/minimals
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` adalah hasil `uv export` dari `uv.lock` — versi persis sama
dengan lokal. **Jangan** `pip install .`: build isolation hatchling butuh
unduhan tambahan dan tidak diperlukan, karena Passenger menambahkan Application
root ke `sys.path` (bukan instal paket).

## 5. Buat `.env`

```bash
cd /home/USER/minimals
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # → SECRET_KEY
chmod 600 .env
```

Isi minimum:

```dotenv
SECRET_KEY=<hasil generate, minimal 32 karakter>
DATABASE_URL=mysql+pymysql://USER:PASS@localhost:3306/USER_minimals
PORT=8000
FLASK_DEBUG=false
FORCE_HTTPS=true
TRUSTED_PROXY=false
MIGRATE_ON_BOOT=false
SEO_INDEXABLE=true
```

Catatan:

- `SECRET_KEY` kosong / <32 karakter / masih placeholder → app **menolak boot**
  (`framework/infra/config.py`).
- `DATABASE_URL` sebenarnya ditulis otomatis oleh wizard di langkah 7, tapi
  mengisinya lebih dulu membuat langkah itu tidak perlu me-repoint engine.
- `TRUSTED_PROXY=false`: Passenger sudah mengisi `HTTPS` dan `REMOTE_ADDR`
  sendiri; ProxyFix tidak dipakai.
- `MIGRATE_ON_BOOT=false`: migrasi dijalankan sekali di langkah 7. Kalau
  `true`, tiap worker Passenger ikut menjalankan Alembic saat boot.

## 6. Cek `passenger_wsgi.py`

cPanel membuat file ini otomatis dengan isi default. Ganti seluruh isinya
dengan versi repo:

```python
from app.create_app import create_app

application = create_app()
```

Passenger meng-import nama `application`; jangan diganti.

## 7. Wizard setup via CLI

Wizard web (`/setup`) **tidak bisa dipakai** di cPanel: `_deny_public_client()`
(`app/infra/setup.py`) hanya menerima klien loopback, dan tidak ada port lokal
untuk di-curl. Pakai wizard terminal — service yang sama, tanpa lapisan HTTP:

```bash
cd /home/USER/minimals
source /home/USER/virtualenv/minimals/3.11/bin/activate
python -m app.cli setup
```

Perintah ini tes koneksi → tulis `DATABASE_URL` ke `.env` → Alembic
`upgrade head` → seed role + admin + brand + bahasa. Aman dijalankan ulang:
kalau sudah selesai ia hanya melaporkan database aktif.

Prompt, validasi, mode non-interaktif, dan troubleshooting: lihat
[`setup-cli.md`](setup-cli.md).

## 8. Restart & verifikasi

```bash
mkdir -p /home/USER/minimals/tmp && touch /home/USER/minimals/tmp/restart.txt
```

Atau tombol **Restart** di Setup Python App.

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/health
curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/ready
curl -s https://app.example.com/ | grep -o '<title>[^<]*</title>'
```

`/health` = proses hidup, `/ready` = database bisa di-query (503 kalau tidak).
Lalu buka domainnya dan login dengan admin dari langkah 7.

## Redeploy (update kode)

```bash
# lokal
yarn build
# upload app/ + app/static/frontend/
```

```bash
# server
source /home/USER/virtualenv/minimals/3.11/bin/activate && cd /home/USER/minimals
pip install -r requirements.txt      # hanya kalau dependency berubah
touch tmp/restart.txt
```

Migrasi skema: **jangan** lewat `MIGRATE_ON_BOOT`. Jalankan sekali:

```bash
FLASK_APP='app.create_app:create_app' flask db upgrade
```

## Troubleshooting

| Gejala | Penyebab / solusi |
|---|---|
| 500 + `SECRET_KEY must be set` | `.env` tidak ada di Application root, atau nilainya <32 karakter. |
| 403 di `/setup` | By design. Pakai langkah 7. |
| Halaman kosong / "frontend not built" | `app/static/frontend/` belum di-upload atau `yarn build` belum jalan. |
| 502 / 503 dari Passenger | Baca `stderr.log` di Application root. Biasanya `ModuleNotFoundError` (venv salah / deps belum install) atau Python <3.11. |
| Redirect loop | `FORCE_HTTPS=true` tapi diakses lewat `http://`. Pakai `https://`, atau set `false` sementara. |
| `database is locked` | SQLite + beberapa worker Passenger. Pindah ke MariaDB (langkah 3–5). |
| Login 400 CSRF | Cookie `Secure` dikirim lewat HTTP. Akses via HTTPS. |
| Aset 404 | `index.html` ada tapi `assets/` tidak ter-upload — upload seluruh folder, bukan hanya `index.html`. |
| Perubahan tidak muncul | `tmp/restart.txt` belum di-touch; Passenger meng-cache proses Python. |

Log aplikasi: `data/app.log` (default `LOG_FILE`). Log Passenger/LiteSpeed:
`stderr.log` di Application root.

## Catatan

- **SQLite tidak disarankan.** Passenger menjalankan lebih dari satu worker;
  penulisan bersamaan akan saling mengunci. Pakai MariaDB.
- **`requirements.txt` adalah artefak generated.** Setiap `pyproject.toml`
  berubah, regenerate dan commit ulang:
  `uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt`
- `data/` dan `app/static/uploads/` harus writable oleh user cPanel (default
  di `/home/USER` sudah begitu).
- `TRUSTED_PROXY` biarkan `false` bahkan di belakang Cloudflare. Flag itu
  hanya mengaktifkan ProxyFix untuk peer privat/loopback, sedangkan di
  Passenger `REMOTE_ADDR` sudah berisi IP klien asli — jadi tidak akan pernah
  aktif. Skema HTTPS sudah benar dari Passenger.
