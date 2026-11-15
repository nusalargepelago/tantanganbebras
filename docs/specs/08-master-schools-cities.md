# 08 — Master Data: Sekolah & Kota/Kabupaten

> Parent: [`00-master-overview.md`](00-master-overview.md)
> Scope: domain `app/school`, API `/api/v1/school` + `/api/v1/city`, integrasi
> dengan onboarding/student/import, dan halaman admin `/schools`.

---

## 1. Entities

### 1.1 `cities`

Kabupaten/kota Indonesia sebagai master **read-only**: `id` (UUIDv7) dan
`name` (UNIQUE, bentuk kanonik `Kota …` / `Kabupaten …`). Tidak ada endpoint
tulis — hanya `GET /api/v1/city` untuk mengisi pilihan di klien.

### 1.2 `schools`

| Column | Notes |
|-------|-------|
| `id` | UUIDv7 PK |
| `name` | UNIQUE lewat normalisasi (`names.normalize_name`) |
| `city_id` | **NOT NULL** FK → `cities.id` — kota melekat pada sekolah |
| `is_active` | deaktivasi menyembunyikan sekolah dari list member |

### 1.3 Kota siswa/guru diturunkan, bukan disimpan

`students` dan `teachers` hanya menyimpan `school_id`. Presenter membaca
`school.city.name`, dan `country` selalu konstan `"Indonesia"`. Kolom free-text
lama sudah di-drop — sejak itu tidak ada lagi jalur menulis kota per murid.

---

## 2. Endpoints

| Method | Endpoint | Akses | Catatan |
|--------|----------|-------|---------|
| GET | `/api/v1/school` | session | `q` (ilike nama); `includeDisabled=1` hanya admin → `{"items": […]}` |
| POST | `/api/v1/school` | session (siapa pun yang login) | `{name, cityId}` → 201 + audit `school_created`; nama duplikat (normalized) → 409 `school_already_exists` |
| PATCH | `/api/v1/school/:id` | admin | `{name?, cityId?, isActive?}` → 200 + audit `school_updated` |
| GET | `/api/v1/city` | session | `{"items": [{id, name}]}` |

Presenter `SchoolOut` = `{id, name, isActive, cityId, city: {id, name}}`.

---

## 3. Aturan bisnis

- **Normalisasi nama** (`app/school/names.py`) menjadi lowercase, spasi tunggal
  — dipakai untuk deteksi duplikat sekolah maupun resolve nama saat import.
- **Create sekolah terbuka untuk user yang login** — tidak lagi admin-only dan
  tidak bergantung pada master kosong. Di halaman onboarding, dropdown sekolah
  menampilkan baris *+ Tambah sekolah* (baris custom creatable) **hanya ketika
  daftar hasil kosong** — master kosong, atau ketikan user tidak cocok dengan
  sekolah manapun (predicate = substring `label`/`value` case-insensitive, sama
  dengan filter bawaan Combobox; `frontend/src/shared/pickerFilter.ts`). Klik
  baris itu membuka dialog *Tambah Sekolah* (`AddSchoolDialog.vue`, nama pra-isi
  dari ketikan + wajib kota, fetch kota lazy); setelah sekolah dibuat, master
  di-refetch dan pilihan itu otomatis terpasang di form. Satu-satunya aturan
  backend: nama unik (normalized — case/spasi-insensitive, termasuk duplikat
  nonaktif) → `409 school_already_exists`. Jalur tulis tetap satu jalan
  (`SchoolService.create_school` → dup-check → `_commit`). Admin tetap
  satu-satunya yang dapat rename/(de)aktifkan (`PATCH /api/v1/school/:id`).
- **Kota mengikuti sekolah.** Form onboarding/siswa hanya memilih sekolah; kota
  tampil read-only dari `school.city`, negara selalu `Indonesia`. `cityId` yang
  tetap dikirim client diabaikan (`extra=ignore`) — tidak pernah bisa
  meng-override.
- **Sekolah nonaktif** hilang dari `GET /school` member (pilihan form ikut
  menyusut), tetap terlihat admin lewat `includeDisabled=1`. Sejak revisi ini,
  nonaktif juga berarti **tidak bisa dipilih**: `require_school()` melempar
  422 `school_inactive` untuk onboarding, create siswa, dan import (baris
  gagal dengan `school_inactive`). `PATCH /student/:userId` dengan `schoolId`
  yang **berubah** juga ditolak; `schoolId` yang identik (full-form payload)
  diabaikan, jadi field lain tetap bisa diedit meski sekolahnya dinonaktifkan
  belakangan.
- **Import XLSX** menyelesaikan nama sekolah ke master; nama yang tidak dikenal
  menjadi error `school_not_in_master`. Kolom `city` lama diabaikan.
- **Error**: 400 `school_name_too_short` / `city_not_in_master`, 404
  `school_not_found`, 409 `school_already_exists`. Service raise exception,
  commit hanya di `ServiceBase._commit()`.

---

## 4. Migrasi

Dua revision bertanggal (konvensi CLAUDE.md §Migrations — skema diubah di
titik masalah, bukan menumpuk history):

| Revision | Perilaku |
|---|---|
| `20261114_8_master_schools_cities.py` | Membangun master `cities` + `schools`, memigrasi data free-text lama ke FK lewat alias-map, lalu menghapus kolom legacy `school`/`city`/`country`. `PRAGMA foreign_keys=ON` di-set dari `autocommit_block()` (di dalam transaksi Alembic PRAGMA = no-op) agar cascade penghapusan akun junk benar-benar jalan di kedua jalur (`flask db upgrade` dan `MIGRATE_ON_BOOT`). |
| `20261114_9_school_city_id.py` | Menambah `schools.city_id` NOT NULL + FK dengan backfill sekolah→kota, lalu menjatuhkan `city_id` per-baris di `students`/`teachers`. Batch rebuild SQLite men-DROP tabel parent sementara child masih me-referensi, jadi `foreign_keys=OFF` di-set dari `autocommit_block()`, di-ON-kan kembali di `finally`, ditutup `foreign_key_check`. Langkah-langkahnya idempoten (kolom/FK/backfill dilewati bila sudah ada) sehingga migrasi yang gagal bisa diulang. |

Jalur test (`db.create_all()`) menanam seed yang sama dengan membaca literal
dari kedua module migration lewat importlib (`tests/conftest._seed_master`) —
skema dan master di test selalu identik dengan production seed.

---

## 5. Frontend

- **`/schools`** (`features/school/`) — admin only: list + pencarian, tambah
  (nama + Combobox kota), edit inline (nama + kota), toggle aktif/nonaktif.
- **`shared/masters.ts`** — `fetchSchools()` / `fetchCities()` dengan cache
  module-level; `invalidateMasters()` dipanggil store sekolah setelah tulis.
- **Form onboarding & siswa** — hanya Combobox sekolah, lalu blok read-only
  berisi kota hasil sekolah terpilih dan negara `Indonesia`
  (`shared.selectSchoolFirst` saat sekolah belum dipilih). Di form onboarding,
  Combobox selalu menyertakan baris *+ Tambah sekolah* saat daftar hasil kosong
  (lihat §3) yang membuka `AddSchoolDialog.vue`.
  (`features/onboarding/views/AddSchoolDialog.vue`)
- **Import** — hint kolom menyebut `school` saja untuk lokasi; kota tidak
  dikirim.

---

## 6. Tests

`tests/test_school.py` meliputi list (session/auth), CRUD admin (create wajib
`cityId`, duplikat 409, pindah kota, 404, 403 non-admin), create non-admin
(saat master kosong/hanya nonaktif/berisi sekolah lain — semua boleh 201;
duplikat → 409 termasuk duplikat nonaktif dan varian case/spasi), serta fakta
`cityId` dari client pada klasifikasi diabaikan — kota selalu kota sekolah.
Dilengkapi `test_onboarding.py::test_client_sent_city_is_ignored` dan
assertion derived city pada `test_student.py`.
