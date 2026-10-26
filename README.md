# Tantangan Bebras

Platform latihan dan kompetisi **Computational Thinking** untuk jenjang
**Siaga, Penggalang, dan Penegak**. Satu aplikasi untuk menyusun bank soal,
membagikan latihan mandiri, menjalankan event terjadwal, dan membaca hasilnya.

Dibangun sebagai satu service Flask yang sekaligus menyajikan SPA Vue 3 — cukup
satu proses, satu database, dan satu container di belakang Caddy, tanpa gateway
dan tanpa layanan tambahan.

> **Status: open alpha.** Sudah dipakai untuk data sungguhan, tetapi skema dan
> kontrak API masih dapat berubah antar versi.

## Peran pengguna

| Peran | Pekerjaan utama |
|---|---|
| **Admin / guru** | Menyusun topik dan soal, menyiapkan latihan dan event, mengelola akun siswa, membaca hasil |
| **Siswa** | Mengerjakan latihan dan event dari ponsel, lalu melihat skor dan pembahasan |
| **Operator** | Memasang, memelihara, mencadangkan, dan memulihkan instalasi |

## Fitur

### Bank soal & topik

- Soal pilihan ganda dan esai dengan konten rich text dan gambar (unggah hingga 5 MiB).
- Kategori **Siaga / Penggalang / Penegak**, tingkat kesulitan, dan status aktif.
- Topik sebagai pengelompokan bab yang bisa diurutkan ulang.
- Editor soal dengan penyimpanan otomatis setiap 3 detik, penanda perubahan yang
  belum tersimpan, dan panel outline untuk berpindah antarsoal.
- Hapus lunak: soal dapat dipulihkan atau dihapus permanen.

### Latihan mandiri

- Satu klik **Mulai Latihan** — sistem menyusun satu lembar berisi soal acak dari
  bank sesuai kategori siswa. Jumlah soal per lembar diatur admin.
- Hitung mundur 30 menit, jawaban tersimpan otomatis, pengumpulan dan penilaian
  otomatis dengan 10 poin per jawaban benar.
- Riwayat latihan lengkap dengan skor, durasi, dan pembahasan tiap soal.

### Event & kompetisi

- Event berisi daftar soal pilihan, batas waktu sendiri, dan tenggat pengumpulan.
- Status **draf / terbit** — soal baru dapat dikerjakan setelah event diterbitkan.
- Setiap percobaan menyimpan salinan soalnya sendiri, sehingga perubahan pada bank
  soal tidak mengubah hasil yang sudah berjalan.
- Halaman hasil untuk guru: skor dan durasi setiap peserta.

### Manajemen siswa

- Data siswa dengan kategori, sekolah, dan kota; aktivasi akun, hapus lunak, dan
  pemulihan.
- Impor massal dari XLSX, lengkap dengan templat yang bisa diunduh.
- Pencarian dan filter berdasarkan kategori maupun status.

### Dasbor & laporan

- Dasbor admin: jumlah soal, siswa, event, dan latihan, plus sebaran sekolah,
  pendaftaran, dan kategori.
- Dasbor siswa: latihan yang sedang berjalan dan riwayat skor.

### Operasional

- **Wizard instalasi pertama** — pilih database, uji koneksi, isi brand, buat
  administrator. Hanya menerima koneksi loopback.
- **White-label & SEO** — nama, tagline, deskripsi, site URL, dan bahasa diatur
  sekali, lalu di-inject server-side ke `<title>`, meta, robots, dan Open Graph.
- **Dua bahasa** — Indonesia dan Inggris, dengan preferensi tersimpan per pengunjung.
- **Backup** — ekspor seluruh database ke SQL dan impor untuk memulihkan.
- **Audit log** untuk perubahan sensitif, serta to-do internal untuk pekerjaan tim.

### Pengalaman siswa

- Tampilan mobile-first dengan navigasi bawah dan mode fokus saat mengerjakan.
- **Panduan interaktif** yang mengantar siswa dari latihan pertama, cara menjawab,
  sampai membaca hasil — lalu menawarkan event sebagai langkah lanjutan.
- Animasi perayaan setiap kali latihan atau event selesai.

## Alur kerja

1. **Siapkan** — admin membuat topik, menulis soal, lalu menyusun latihan atau event.
2. **Kerjakan** — siswa masuk dan mengerjakan latihan kapan saja, atau event pada
   jendela waktunya.
3. **Baca hasil** — skor pilihan ganda dihitung otomatis; guru melihat rekap peserta
   di halaman hasil.

## Teknologi

| | |
|---|---|
| **Backend** | Flask 3 · SQLAlchemy 2 · Pydantic 2 · Alembic · waitress |
| **Frontend** | Vue 3 · Vite · Pinia · frappe-ui · Tailwind (TypeScript strict) |
| **Database** | SQLite · MariaDB/MySQL · PostgreSQL |
| **Deploy** | Docker (non-root) + Caddy (TLS) |

## Menjalankan di lokal

```bash
uv sync
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # → SECRET_KEY
uv run python -m app.run                                   # waitress di :8000
```

`SECRET_KEY` wajib minimal 32 karakter; placeholder ditolak dan aplikasi menolak
boot. Untuk pengembangan lewat HTTP biasa, set `FORCE_HTTPS=false` agar tidak
terjadi loop redirect.

Frontend dikembangkan terpisah saat mengubah antarmuka:

```bash
cd frontend
yarn install
yarn dev        # Vite :5173, proxy /api → :8000
yarn build      # hasil build ke app/static/frontend/
yarn typecheck
```

Pengujian dan lint:

```bash
uv run pytest
uv run ruff check .
```

## Instalasi pertama

Selama setup belum selesai, semua navigasi diarahkan ke `/setup`. Wizard hanya
menerima klien loopback — jalankan dari server, atau lewat SSH tunnel:

```bash
ssh -L 8000:localhost:8000 server
# lalu buka http://127.0.0.1:8000/setup
```

Wizard menulis `DATABASE_URL` ke `.env`, memigrasi database target, membuat
administrator, dan menyimpan brand beserta bahasa.

## Deploy produksi

Siapkan aset frontend terlebih dahulu:

```bash
cd frontend && yarn install && yarn build
```

1. Isi `.env`: `SECRET_KEY` asli, `DATABASE_URL`, dan `SEO_INDEXABLE`.
2. Arahkan Caddy ke `localhost:8000` — contoh konfigurasi ada di `Caddyfile`.
3. Di belakang proxy, set `TRUSTED_PROXY=true` dan biarkan `FORCE_HTTPS=true`
   selama Caddy mengirim `X-Forwarded-Proto`.
4. Jalankan `uv run python -m app.run`, atau set `MIGRATE_ON_BOOT=true` bila ingin
   migrasi berjalan otomatis saat start.

Dengan Docker:

```bash
docker compose up --build
```

Port di-bind ke `127.0.0.1:8000` dengan Caddy di depan. Bila memakai SQLite pada
volume host, pastikan `./data` dapat ditulis uid `10001`:
`sudo chown -R 10001:10001 data`. Database di dalam container tidak persisten —
set `DATABASE_URL` di `.env`.

## Keamanan

Beberapa hal yang perlu dibaca sebelum instalasi dibuka ke internet:

- `/uploads/*` disajikan tanpa autentikasi — jangan menyimpan berkas sensitif di sana.
- Pendaftaran akun staf terbuka secara default dan langsung membuat sesi; tutup lewat
  `PUT /api/v1/auth/registration` untuk instalasi invite-only.
- `/health`, `/ready`, dan `/api/v1/setup/status` bersifat publik dan menampilkan
  informasi terbatas tentang instalasi.
- Rate limit berjalan per IP; untuk deployment multi-worker, arahkan
  `RATE_LIMIT_STORAGE_URL` ke Redis.
- CSRF, CSP/HSTS, dan audit log aktif secara default; password di-hash dengan scrypt.

## Dokumentasi

- [`CLAUDE.md`](CLAUDE.md) — konvensi kode, arsitektur berlapis, wire format, dan
  daftar endpoint lengkap.
- [`docs/FEATURES.md`](docs/FEATURES.md) — matriks fitur beserta tautan ke
  spesifikasi tiap domain.
- [`framework/README.md`](framework/README.md) — base class dan utilitas framework.

## Kontribusi

Selama open alpha, kontribusi dibatasi pada perbaikan bug — issue dan PR perbaikan
diterima, fitur baru belum.

## Lisensi

[MIT](LICENSE) — © 2026 Apriliansyah Idris.
