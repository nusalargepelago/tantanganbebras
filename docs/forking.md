# Forking Minimals

Minimals **open alpha**: skema & kontrak masih bisa berubah. Fork yang sehat
memperpanjang master, bukan menulis ulang. Dokumen ini adalah aturan generik
untuk **semua fork** — di-inherit otomatis saat fork merge `master`.
`FORK.md` di root fork menyimpan selisih yang spesifik fork.

## 1. Prinsip

- **master = satu-satunya sumber kebenaran** untuk perilaku shared.
- Fork mengubah shared files hanya sebagai **lapisan aditif** (blok/field/
  route tambahan), tidak menggantikan isi master dengan versinya sendiri.
- Fork-only features hidup di **file fork-owned** (`A` di git), bukan edit
  inline di file bersama.
- Konflik adalah sinyal kebocoran desain: kalau file yang sama diedit master
  dan fork berulang kali, delta fork harus dipindah ke file fork-owned atau
  di-upstream-kan ke master.

## 2. Aturan keras

1. Merge hanya `master` → fork (`git merge master`), atau rebase bila branch
   fork privat. Jangan pernah merge fork → master.
2. Resolusi konflik: **master skeleton menang**; delta fork di-re-apply aditif
   di atasnya atau dipindah ke file fork-owned. Jangan "keep mine" untuk file
   milik master.
3. Jangan `-X ours/-X theirs`, `merge=ours` di `.gitattributes`, atau
   `git checkout --ours/--theirs` massal.
4. Jangan "menghapus kembali" yang master tambahkan — bersembunyi di level
   route/nav/config, bukan hapus di shared file.
5. Kalau test fork gagal karena **kontrak master berubah**, perbaiki test fork
   ke kontrak baru — jangan revert master.
6. `.env` tidak pernah di-commit; secret tidak pernah masuk repo.
7. `FORK.md` diperbarui di commit yang sama dengan perubahan shared file
   fork atau penambahan file fork-owned.
8. Konflik yang tidak sesuai tabel resolusi → **STOP, tanya owner**.

## 3. Prosedur merge

```bash
git status                                # fork HARUS bersih (WIP di-commit/stash)
git fetch origin && git log --oneline master -5
git merge --no-commit --no-ff master
git diff --name-only --diff-filter=U      # daftar file konflik → tabel resolusi di FORK.md
# resolve → verifikasi (wajib hijau, laporkan angkanya):
uv run pytest
uv run ruff check .
cd frontend && yarn typecheck && yarn build
git commit -m "merge(master): adopt <ringkas>"
```

Setelah merge, fork dengan migrasi sendiri menjalankan fresh-boot (`flask db
upgrade` di sqlite scratch) — master boleh mengedit `0001_initial.py` langsung
(alpha), pastikan revisi fork setelahnya tetap nyambung.

### Fork yang belum mau commit WIP (mis. labba) — stash protocol

Kalau fork sengaja **belum** commit WIP sebelum merge, gunakan stash — dengan
batas yang jelas:

```bash
git stash push --include-untracked -m "wip before merge master <yymmdd>"
git merge --no-commit --no-ff master
# resolve → verifikasi hijau (lihat di atas)
git commit -m "merge(master): adopt <ringkas>"
git stash pop          # konflik pop mungkin — resolve aditif, master wins skeleton
# verifikasi ulang (pytest + typecheck + build), lalu selesai
```

Yang **tidak** bisa di-stash:

- **Unmerged index entries** (merge half-done / index korup tanpa `MERGE_HEAD`) —
  `git stash` menolak atau gagal total. Heal dulu: commit WIP, atau restore
  konten stage 3 ke worktree lalu `git add`. Untuk labba ini **langkah wajib**
  sebelum prosedur apa pun di atas.
- File `.gitignore`d (`data/`, `app/static/frontend/`, `node_modules/`) dan
  submodule.
- Apa pun di luar worktree.

Aturan tetap:

- Jangan `git stash --keep-index`; jangan stash saat index half-merged.
- `git stash pop` bisa memunculkan konflik dengan hasil merge — resolve aditif.
- Jangan `git stash drop` sebelum suite hijau + build lulus setelah pop.
- Setelah pop, jalankan ulang `uv run pytest` + `yarn typecheck && yarn build`.
- Kalau pop kacau: `git stash branch wip-<tanggal>` memindahkan WIP ke branch baru.

Preferensi tetap: **commit WIP (atau branch WIP) > stash > jangan merge**.
Stash adalah alat untuk fork yang sadar risikonya, bukan jalan pintas.

## 4. Peta resolusi konflik

| Situasi | Rule |
|---|---|
| **modify/modify** shared view/store/dto | Master wins skeleton; re-apply delta fork aditif (blok baru setelah blok master) atau pindah ke file fork-owned + route swap |
| **add/add** (master & fork bikin file yang sama) | Master wins sebagai base; versi fork pindah ke path fork-owned, atau delta fork di-reapply aditif ke file master |
| **modify/delete** (fork hapus file master) | **Master wins — file direstore.** Fork menyembunyikan via route/nav |
| **lockfile** (`uv.lock`, `yarn.lock`) | Jangan hand-merge; setelah merge jalankan `uv lock` / `yarn install`, commit hasilnya |
| **locales** `en.json`/`id.json` | Additive keys; **parity en↔id wajib**; jangan sentuh kunci `auth.passwordRules.*` / `route.*` milik master |
| **migrations** | Revisi fork selalu jalan setelah `0001_initial.py`; fork tidak boleh mengedit `0001` — itu hak master |
| **docs** `CLAUDE.md`/`README.md` | Master otoritatif; fork menambah section sendiri. Tabel endpoint CLAUDE.md → `tests/test_docs.py` harus hijau; tambah baris fork, jangan matikan testnya |
| **deps** `pyproject.toml`/`package.json` | Union; butuh `uv lock` / `yarn install` ulang, jangan hand-resolve |
| **framework/** | Sangat sensitif: master wins defaultnya; delta fork hanya aditif |

## 5. Contoh drift kontrak yang paling sering memukul fork

Fork harus ikut **tanpa revert master**:

- `/api/v1/setup/status` publik → `{setupRequired, reason}` saja; detail
  `activeEngine`/`activeUrl` (password di-mask) hanya untuk klien loopback.
  Client/store fork menyesuaikan (field opsional); test fork diupdate ke
  kontrak ini.
- `UserAdminOut` adalah subclass `UserOut`; field output sama.
- List users admin: `distinct(User.id)` untuk total + bare-id pagination —
  fork tidak perlu mengubah apa pun; jangan ganti `.count()` kembali.
- `require_owner_or_role` dipakai untuk `GET /account/users/:id`.

## 6. Security invariants (wajib lolos tiap merge)

- Setup wizard hanya loopback — raw peer + effective address + hop terakhir XFF
  semuanya loopback (`app/infra/setup.py`).
- `/setup/status` publik tidak mengekspos engine/DB URL.
- CSRF exemption list tidak bertambah kecuali terdokumentasi; `audit_log`
  dipanggil di setiap write penting.
- Endpoint write fork: `@login_required` + gate role yang sesuai + `audit_log`.
- API key: bcrypt + prefix lookup; raw key hanya sekali. Jangan pernah di log.
- Tidak ada secret hard-coded; `.env` di luar repo.

## 7. Ekstraksi reusable ke master (upstream)

Kalau fork menemukan primitive yang layak di-share (komponen, test helper,
config default yang generik):

1. Buka issue/usulan ke maintainer master.
2. Master menyerap sebagai PR terpisah; fork menyimpan copy fork-owned **sampai**
   master menyerapnya — jangan hapus di fork sebelum upstream ada.
3. Setelah upstream merge, fork hapus copy fork-owned pada merge berikutnya.

`docs/FORK.template.md` adalah kerangka `FORK.md` yang dipakai tiap fork.

## 8. Checklist verifikasi & format laporan

Setelah resolve, **wajib** hijau + laporkan:

```
uv run pytest            # x/y passed (sebutkan angkanya)
uv run ruff check .      # clean
cd frontend && yarn typecheck
cd frontend && yarn build
```

Format laporan: master sha yang diadopsi · daftar file konflik & cara resolve ·
jumlah test sebelum/sesudah · file yang direstore manual · apa yang tidak
dikerjakan + alasannya.

## 9. Pembagian kepemilikan (siapa mengedit apa)

| Area | Fork boleh | Fork tidak boleh |
|---|---|---|
| Domain baru (`app/<domain>/`) | Bebas (pola 7-file + register blueprint sebelum `register_spa` + `db.create_all()` di `create_app`) | Skip `models.py` import di `create_app.py` |
| Feature baru (`frontend/src/features/<x>/`) | Bebas | Menyunting view master sebagai gantinya |
| `frontend/src/shared/*` | Tambah file fork-owned; edit hanya aditif | Menghapus/mengubah kontrak primitive master |
| Route & guard | Aditif (route fork + guard fork) | Reorder urutan auth guard / mengganti redirect guestOnly |
| `app/migrations/versions/` | Revisi baru untuk fork | Edit `0001_initial.py` |
| Brand/default (`setup_dto.py`, `brand.ts`) | Bebas (itu keputusan produk fork) | Mengganti kontrak SEO/`settings` master |
| `CLAUDE.md` / `README.md` | Section fork additive | Rewrite isi master |
