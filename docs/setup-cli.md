# Setup pertama via CLI

Wizard yang sama dengan `/setup`, dijalankan dari terminal. Dipakai kalau
tidak ada loopback hop ke aplikasi: **cPanel/Passenger**, VPS headless, atau
container yang port-nya tidak di-publish.

Alasannya: `POST /api/v1/setup` dijaga `_deny_public_client()`
(`app/infra/setup.py`) yang hanya menerima klien loopback, karena endpoint itu
tanpa autentikasi bisa menulis `DATABASE_URL` ke `.env` dan membuat
administrator. Di Passenger `REMOTE_ADDR` berisi IP klien asli dan tidak ada
port lokal untuk di-tunnel, jadi wizard web selalu 403 — termasuk untuk pemilik
server. Perintah di bawah memanggil service yang sama, tanpa lapisan HTTP.

## Prasyarat

- Dependency sudah terpasang di venv aktif (`pip install -r requirements.txt`).
- `.env` sudah ada dan berisi `SECRET_KEY` ≥32 karakter. `create_app()`
  membaca config saat import, jadi `SECRET_KEY` kosong akan gagal sebelum
  prompt pertama muncul.
- Database (MySQL/MariaDB/PostgreSQL) dan user-nya sudah dibuat — wizard hanya
  memverifikasi koneksi, tidak membuat database.

## Menjalankan

```bash
source /home/USER/virtualenv/minimals/3.11/bin/activate && cd /home/USER/minimals
python -m app.cli setup
```

Lewat Flask CLI juga bisa:

```bash
FLASK_APP='app.create_app:create_app' flask setup
```

Kalau setup sudah pernah selesai, perintah ini hanya mencetak database aktif
lalu keluar dengan status 0 — aman dijalankan berulang.

## Prompt

| Prompt | Default | Catatan |
|---|---|---|
| Database engine | `mariadb` | `mariadb` \| `sqlite` \| `postgresql` |
| Host | `localhost` | |
| Port | `3306` / `5432` | Mengikuti engine |
| Database name | — | Nama database yang sudah dibuat |
| Database user | — | User yang punya akses ke database itu |
| Database password | — | Tidak ditampilkan |
| SQLite path | `data/app.db` | Hanya untuk engine `sqlite`; kosongkan untuk default |
| Admin email | — | |
| Admin username | dari email | Kosongkan untuk memakai bagian lokal email |
| Full name | — | |
| Admin password | — | Diminta dua kali, tidak ditampilkan |
| Brand name | `Minimals` | |
| Tagline | kosong | |
| Description | kosong | |
| Site URL | kosong | Harus URL absolut `http(s)://` |
| Language | `en` | `en` \| `id` |

Validasi yang mengulang prompt, bukan menggagalkan seluruh proses:

- **Koneksi database** dites sebelum lanjut. Gagal → pesan error, lalu ditanya
  mau coba database lain atau batal.
- **Blok admin** diulang dari email kalau password tidak memenuhi kebijakan:
  minimal 8 karakter, ada huruf besar, huruf kecil, angka, dan simbol
  (`app/infra/validation.py`).
- **Site URL** ditanya ulang kalau bukan URL absolut.

## Yang diubah

1. `DATABASE_URL` ditulis ke `.env` — hanya kalau target berbeda dari engine
   yang sedang aktif.
2. Migrasi Alembic dijalankan sampai `head` pada database target.
3. Seed: role `Member`, user admin, brand (`name`, `tagline`, `description`,
   `siteUrl`), dan `appLang`.

## Setelahnya

```bash
touch tmp/restart.txt          # Passenger memuat ulang .env
curl -s -o /dev/null -w '%{http_code}\n' https://app.example.com/ready
```

`/ready` = 200 berarti database baru sudah terpakai. Lalu login dengan akun
admin yang barusan dibuat.

## Non-interaktif

Untuk otomasi, panggil service-nya langsung — DTO-nya sama dengan yang dipakai
wizard web:

```bash
python - <<'PY'
import os
from app.create_app import create_app
from app.infra.setup_dto import SetupIn
from app.infra.setup_service import SetupService

app = create_app()
with app.app_context():
    print(SetupService().run(SetupIn.validate({
        "db": {
            "engine": "mariadb",
            "host": "localhost",
            "database": os.environ["DB_NAME"],
            "username": os.environ["DB_USER"],
            "password": os.environ["DB_PASS"],
        },
        "admin": {
            "email": os.environ["ADMIN_EMAIL"],
            "password": os.environ["ADMIN_PASS"],
            "fullName": os.environ["ADMIN_NAME"],
        },
        "brand": {"name": "Minimals", "siteUrl": "https://app.example.com"},
        "lang": "id",
    })))
PY
```

## Troubleshooting

| Pesan | Arti |
|---|---|
| `setup is already complete` | Sudah ada user di database aktif. Tidak ada yang diubah. |
| `invalid db credentials` | User/password salah, atau user belum diberi akses ke database itu. |
| `db not found` | Nama database salah / belum dibuat di cPanel. |
| `unsupported host` | Host resolve ke alamat link-local (metadata cloud) — ditolak. |
| `password must contain ...` | Kebijakan password; blok admin diulang. |
| `site url invalid` | Bukan URL absolut `http(s)`, atau mengandung spasi. |
| `SECRET_KEY must be set ...` | `.env` belum ada / nilainya <32 karakter; tidak sampai ke prompt. |
| `ModuleNotFoundError` | Venv belum aktif atau `pip install -r requirements.txt` belum jalan. |
