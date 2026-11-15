# FORK.md — <nama fork>

Fork dari **minimals** (upstream: `master`). Aturan generik: baca
**`docs/forking.md`** dulu — file ini hanya berisi selisih yang spesifik fork.

- Produk fork: <satu dua kalimat>
- Maintainer: <nama>
- Base snapshot: master `<sha>` · diadopsi <tanggal>
- Fork di depan: <N> commit · terakhir sync: <tanggal/sha>

> Cara pakai: copy file ini ke `FORK.md` di root fork, isi semua `<...>`,
> hapus placeholder yang tidak relevan. Perbarui di commit yang sama dengan
> perubahan shared file / file fork-owned baru.

## 1. Identitas & domain fork

<Deskripsi fitur fork dan alasan fork ada. Tautkan spec/doc utama.>

## 2. Inventaris fork-owned (file baru — tidak akan konflik)

**Backend — domain baru** (pola 7-file master, register di `create_app.py`
sebelum `register_spa`):

- `app/<domain>/` …
- Migrasi fork-owned (setelah master `0001_initial.py`): `<file>`

**Frontend — feature baru:**

- `src/features/<x>/` …
- Komponen/composable shared fork-owned: …

**Docs & tests fork-owned:**

- `docs/…`, `tests/test_<khusus-fork>.py`

**Reusable — kandidat upstream** (lihat §7 forking.md; jangan dipakai
upstream sebelum diserap master):

| Item | Alasan | Status |
|---|---|---|
| … | … | kandidat / fork-only |

## 3. Shared files yang dimodifikasi fork — tabel resolusi

Saat master juga menyentuh file yang sama: **master wins skeleton**, delta fork
re-apply aditif. (Isi dari `git diff master..HEAD --stat` saat ini; snapshot
<tanggal>.)

| File | Delta fork | Cara resolve |
|---|---|---|
| `frontend/src/app/navigation.ts` | item nav fork | Master skeleton; spread item fork **di bawah** item master |
| `frontend/src/app/locales/{en,id}.json` | kunci fork | Aditif + parity en↔id |
| `frontend/src/app/router/{index.ts,guard.ts}` | route/guard fork | Aditif; master wins skeleton (urutan guard jangan diubah) |
| `frontend/src/features/dashboard/views/AdminDashboardView.vue` | … | Master wins; fork delta dipindah ke file fork-owned + route swap |
| `app/create_app.py` | register bp/model fork | Aditif; blok fork terpisah setelah blok master |
| `pyproject.toml` / `uv.lock` | dep fork | Union; `uv lock` ulang |
| … | … | … |

## 4. File yang fork hapus

| File | Aturan resolve saat master memodifikasi |
|---|---|
| `<file>` | Master wins — file direstore; fork sembunyikan via route/nav |

## 5. Kontrak drift — yang harus diupdate di fork, bukan di-revert

- <contoh: `/api/v1/setup/status` publik → minimal shape; update test fork>
- …

## 6. Footguns fork ini

<Daftar hal yang mudah salah saat merge: file yang sering drift, file WIP,
kontrak yang pernah berubah, ketergantungan implisit.>
Kalau fork punya WIP yang sengaja belum di-commit: ikuti **stash protocol**
di `docs/forking.md` §3. Catatan kerasnya: unmerged index entries tidak bisa
di-stash — heal dulu.

## 7. Security checklist tambahan fork

<Delta security khusus fork di luar forking.md §6, mis. endpoint write fork
dan gating-nya.>

## 8. Rencana re-align (bila fork menyimpang dari pola master)

<Langkah konkret untuk mengembalikan file shared ke versi master + memindah
delta fork. Estimasi, risiko, dan status approval.>

## 9. Riwayat merge (append-only)

| Tanggal | Master sha | Konflik & resolve | Verifikasi (pytest/typecheck/build) |
|---|---|---|---|
| … | … | … | … |
