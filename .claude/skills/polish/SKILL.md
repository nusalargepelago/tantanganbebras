---
name: polish
description: >-
  Kanon cosmetics & presentasi untuk UI Minimals (Vue 3 + frappe-ui
  1.0.0-rc.2). Pakai saat bikin, styling, atau me-review UI frontend — view
  baru, komponen, dialog/toast/form/selection — biar tidak drift dari design
  system. Berisi token cheat-sheet (tipografi, radius, focus, warna), pola
  pemakaian komponen kanonik (termasuk list pages), dan drift checklist.
---

# Polish — Kanon Cosmetics & Presentasi

Skill ini merangkum design system yang benar-benar terpasang:
`frappe-ui@1.0.0-rc.2` + Tailwind preset-nya. Token di bawah ini dibaca dari
`frontend/node_modules/frappe-ui/tailwind/tokens/` dan
`tailwind/tokens/provenance.json`.

**Kalau ada yang beda dari kode existing, itu drift** — atau code-only
extension yang disengaja. Tidak ada kategori ketiga.

## Kapan pakai

- **Pakai** saat: bikin view/komponen Vue baru, styling (class Tailwind),
  memasang Dialog/Toast/Form/Select, atau me-review UI dari sisi tampilan.
- **Jangan pakai** untuk: logika backend, migrasi DB, business rules, atau
  data layer (pakai `wiring`).

---

## 1. Token

### Tipografi

Font **Inter Variable**. Regular weight = **420** (bukan 400) — sudah
built-in, jadi `font-normal` bahkan tidak ada di preset.

**Dua keluarga, dibedakan line-height:**

- **UI / heading / label** → `text-<size>` — LH **1.35**. Untuk judul, label,
  chip, teks kompak.
- **Paragraf / body** → `text-p-<size>` — LH **1.5–1.6**. Untuk teks mengalir
  yang dibaca.

Ukuran (px) sama, LH beda: `text-base` (14/1.35) vs `text-p-base` (14/1.5).
Pilih sesuai peran teks, bukan asal ukuran.

**Skala `text-*`:** `2xs` 11 · `xs` 12 · `sm` 13 · `base` 14 · `md` 15 ·
`lg` 16 · `xl` 17 · `2xl` 18 · `3xl` 20 · `4xl` 24 · `5xl` 26 · `6xl` 28 ·
`7xl` 32 · `8xl` 40 · `9xl` 44 · `10xl` 48 · `11xl` 52 · `12xl` 56

**Skala `text-p-*`** (LH dijaga longgar): `2xs` 1.6 · `xs` 1.6 · `sm` 1.5 ·
`base` 1.5 · `md` 1.5 · `lg` 1.5 · `xl` 1.5 · `2xl` 1.5 · `3xl` 1.48 ·
`4xl` 1.4

**Weight variant** — `WEIGHT_VARIANTS = medium (500) · semibold (600) ·
bold (700)`. Semua size punya ketiga varian; `regular` (420) tetap bare
`text-<size>` / `text-p-<size>`.

- Medium/semibold → token gabung: `text-base-medium`, `text-2xl-semibold`,
  `text-p-sm-medium`. **Bukan** `text-base font-medium` — letter-spacing
  di-track terpisah per (size, weight) dan tidak bisa mengikuti `font-weight`.
- `black` **tidak** di-emit (sudah di-drop dari library).

**Pemakaian di repo ini**: judul halaman = `text-2xl-semibold` (Login,
Register, Dashboard). Body/deskripsi = `text-p-sm`. Label field =
`text-base-medium`. Sub-judul kartu = `text-xl-semibold`.

### Radius

Nomor = canonical. Alias bernama sudah tidak ada di rc.2 — jangan pakai
`rounded`, `rounded-sm/md/lg/xl/2xl`.

| Canonical | px | | Canonical | px |
|---|---|---|---|---|
| `rounded-0` | 0 | | `rounded-5` | 10 |
| `rounded-1` | 4 | | `rounded-6` | 12 |
| `rounded-2` | 5 | | `rounded-7` | 16 |
| `rounded-3` | 6 | | `rounded-8` | 20 |
| `rounded-4` | 8 | | `rounded-9` | 100 |

Plus `rounded-none` (=0) dan `rounded-full` (9999px, untuk avatar/ikon chip).

Kanity yang dipakai repo: `rounded-6` untuk panel/kartu, `rounded-4` untuk
elemen kecil, `rounded-full` untuk avatar.

### Focus ring

Focus indicator **default sudah global** di base layer:

```
:focus-visible { outline: var(--focus-outline-default); outline-offset: 0 }
```

2px light / 3px dark. Elemen interaktif baru otomatis dapat ring.

- **Jangan** tambah `focus:ring-2` / `focus-visible:ring` per komponen —
  bentrok dengan `shadow-*`, dan lebar default Tailwind bukan token yang benar.
- Suppress: `focus-visible:outline-none` (panel dialog, ghost input).
- Retheme: `focus-visible:focus-ring-<color>` — color tersedia: `red`, `green`,
  `amber`, `blue`, `violet` (plus `.focus-ring` untuk default).
- Non-focus state (mis. menu terbuka): `data-[state=open]:focus-ring`.

### Warna

Dua sumbu semantik — `variant` + `theme` (lihat Button/Badge). Jangan bikin sumbu
ketiga.

Ramp warna: `gray`, `blue`, `green`, `red`, `amber`, `violet`, `yellow`,
`orange`, `teal`, `cyan`, `purple`, `pink`.

Tiga keluarga semantik (semua theme-aware, light & dark):

| Keluarga | Isi | Pakai untuk |
|---|---|---|
| `surface-*` | `base`, `sidebar`, `elevation-1/2/3`, `gray-1…10`, + 13 ramp warna `1…10` | latar |
| `ink-*` | `base`, `gray-1…9`, + 13 ramp `1…9`, `blue-link` | teks |
| `outline-*` | `base`, `gray-1…9`, + 13 ramp `1…10`, `elevation-1/2`, `outline-alpha` | border |

- Skala **makin besar = makin kuat** (surface-10 paling pekat, ink-9 paling
  gelap). Ikuti ramp yang ada; jangan warna arbitrer (`text-[#...]`).
- Teks butuh perhatian (error, required): `text-ink-red-6`.
- Link: `text-ink-blue-link`.

### Ikon

- String `lucide-<name>` (mis. `icon-left="lucide-log-in"`, atau
  `<span class="lucide-package size-6" />`) — dirender via plugin, tanpa
  import. Default size `size-4`.
- Bisa juga pass Vue `Component` untuk ikon non-Lucide.
- Konstruksi dinamis `` `lucide-${x}` `` **tidak** ke-scan JIT → class tidak
  ter-emit. Pakai literal atau whitelist.

### Spacing & breakpoint

- Spacing: semua integer 0.5–128 (step 0.25rem) — `h-17` valid di preset
  ini, bukan seperti stock Tailwind.
- Breakpoint: `sm` 640 · `md` 768 · `lg` 1024 · `xl` 1280.

---

## 2. Pola pemakaian komponen

### Aturan #0 — native HTML interaktif → komponen frappe

Setiap elemen HTML **interaktif / form** pakai komponen frappe-ui, bukan tag
native. Native `<button>`/`<input>`/dst kehilangan token tema, focus ring
global, dan a11y.

```bash
grep -rnE "<(input|button|select|textarea|label|dialog|table)\b" src/
```

| ❌ Native | ✅ Komponen | Catatan |
|---|---|---|
| `<button>` | `<Button>` | prop `label` = nama a11y (jadi `aria-label`); **jangan** attr `aria-label` — ketimpa. Icon-only: `icon` / slot `#icon`. Link internal: `route`; eksternal: `href` |
| `<input type=text\|email\|search\|tel\|url\|number>` | `<TextInput>` | `type` diteruskan |
| `<input type=password>` | `<Password>` atau `TextInput type=password` | |
| `<input type=checkbox>` | `<Checkbox>` (kontrol) / `<Switch>` (toggle on-off) | `v-model` |
| `<input type=radio>` | `<Radio>` | |
| `<input type=range>` | `<Slider>` | |
| `<textarea>` | `<Textarea>` | |
| `<select>` | `<Select>` (statis) / `<Combobox>` (searchable) / `<MultiSelect>` (banyak) | lihat Selection |
| `<label>` manual | prop `label` di input | |
| modal manual | `<Dialog>` atau `dialog.*` | |
| `<a>` yang "kelihatan tombol" | `<Button :route>` / `<Button :href>` | |

**Native yang DIBIARKAN:**

- `<form>` + `@submit.prevent` — tidak ada `<Form>` pengganti, ini pola benar.
- Elemen **struktur/teks non-interaktif**: `<div>`, `<span>`, `<p>`, `<h1..6>`,
  `<ul>/<li>`, `<header>/<main>/<section>`, dll.
- `<a>` / `<router-link>` untuk navigasi teks biasa.
- Elemen tanpa padanan frappe — boleh native, tapi styling tetap pakai token
  (`bg-surface-*` / `text-ink-*`) supaya theme-aware.

### Dialog

Satu komponen `<Dialog>`; `role="dialog"` selalu.

- Visibility: **`v-model:open`**.
- Prop **flat**: `open`, `title`, `message`, `icon`, `theme`, `size`, `position`,
  `actions`, `dismissible`, `showCloseButton`, `bare`.
- `theme`: `amber` · `blue` · `red` · `green` — Abandon pada header icon badge.
- Slot: `#default` (expose `{ close }`), `#title`, `#actions` (expose
  `{ close, actions }`).
- `DialogAction.onClick` menerima `{ close }` dan **return `void`** — pakai
  block body, bukan expression yang mengembalikan nilai.
- **Imperative** (confirm/alert/prompt dari non-komponen):
  - `dialog.confirm({ title, message, onConfirm })`
  - `dialog.danger({...})` — preset merah + label "Delete" + alert-triangle
  - `dialog.prompt({ fields, onConfirm })`
  - Lifecycle: `onConfirm` **resolve → auto-close**; **throw → tetap terbuka**
    + pesan error inline. `ctx.setError()` tanpa throw **tidak** mencegah
    auto-close.
- Butuh `<FrappeUIProvider>` membungkus app (sudah ada di `App.vue`; plugin
  `app.use(FrappeUI)` di `main.ts` ikut di-`install`).

### Toast

- Imperatif: `toast.success/error/info/warning/message/loading/promise`.
- **`duration` dalam MILIDETIK**. Default **4000ms**.
- Pola loading→hasil (reuse `id`):

```ts
const id = toast.loading('Menyimpan…')
try {
  await save()
  toast.success('Tersimpan', { id })
} catch (e) {
  toast.error(getErrorMessage(e), { id })
}
```

- Message dirender sebagai **teks polos**.

### Inputs / Form

Pakai `TextInput`, `Textarea`, `Password`, `Checkbox`, `Switch`, `Rating`,
`Slider`, atau `FormControl` (dispatcher by `type`).

- Shared labeling props di semua input: **`label`, `description`, `error`,
  `required`**. `id` auto.
- `error` (string | Error | Error[]) → `text-ink-red-6`, set `aria-invalid`,
  dan **menyembunyikan `description`**.
- Variant text-input: **`subtle` | `outline` | `ghost`**. Size:
  `xs` 24 · `sm` 28 · `md` 32 · `lg` 40.
- `v-model` via `defineModel`.
- `FormControl` = dispatcher tipis; set `type` dan ia me-forward
  `label`/`description`/`error`/`required`/`size`/`variant` + attrs ke child.
  Untuk yang butuh prop khusus (`options`, `min`/`max`), pakai komponen
  langsung.

### Selection (Dropdown / Select / Combobox / MultiSelect)

| Kebutuhan | Komponen |
|---|---|
| Menu **aksi** (rename/delete/submenu/switch) | `Dropdown` |
| Pilih 1 nilai, list statis kecil | `Select` |
| Pilih 1 nilai, **searchable** / create-new | `Combobox` |
| Pilih **banyak** nilai | `MultiSelect` |

Aturan bersama:

- Value: `v-model`; visibility: **`v-model:open`**.
- Opsi: `string` atau `{ label, value, disabled?, icon?, description? }`.
  `value` = `string | number`; `''` sah sebagai nilai "none".
- Slot item: **`#item-prefix`, `#item-label`, `#item-suffix`**. Untuk opsi
  yang dibangun di JS: `item.slots.{prefix,label,suffix}`.
- Positioning: **`side`** (`top|right|bottom|left`) + **`align`**
  (`start|center|end`) + `offset` (px) + `portalTo`.
- Grouping menu (`Dropdown`): **`{ group, options }`**.
- `Dropdown` = menu button semantics, `selected` cuma visual (tidak ada
  checkmark). `Select`/`Combobox`/`MultiSelect` = listbox, checkmark built-in.
- Opsi `disabled`: skip keyboard, tak bisa diklik, tak emit.

### Popover

Floating panel umum (filter, color picker, chrome custom) — **bukan** untuk
picker nilai (pakai Select/Combobox), menu aksi (Dropdown), atau hover
(HoverCard).

- `#trigger` sudah as-child (click/keyboard/aria otomatis) — **jangan**
  hand-wire `@click`. Content di `#default`, atau `bare` untuk tanpa shell.
- Visibility `v-model:open`. Props: `side`, `align`, `offset`, `dismissible`,
  `autoFocus`, `trigger` (`click` | `manual`), `reference`, `matchTriggerWidth`.
- `trigger="manual"` = tidak ada `aria-expanded`/`aria-controls`; hanya
  `v-model:open` yang buka/tutup.
- Styling lewat hook `data-slot="content"` dll. — **bukan** prop
  class-injection.

### Provider

`<FrappeUIProvider>` membungkus app sekali (sudah di `App.vue`) — menyediakan
shared components + host `<Toaster>` + `<Dialogs/>`. Wajib untuk `toast.*` dan
`dialog.*`. `app.use(FrappeUI)` di `main.ts` hanya memasang plugin-nya.

---

## 2a. List pages — presentasi (kanonik)

Halaman list di repo ini (`shared/components/List*` + `useListControls`) punya
geometri tetap. Yang dilanggar di sini yang paling cepat terlihat "kurang rapi":

- **Satu wrapper `<div>` polos** untuk `List` + `ListFoot`. Jangan biarkan
  `space-y-4` container memisahkan baris terakhir dari pagination — foot harus
  `mt-1` nempel ke list dan keduanya terlihat satu blok (header
  `rounded-t-6`, foot `rounded-b-6`).
- **`class="list-row-px-3"` wajib di `<List>`** — satu nilai mengalir ke
  header & semua baris lewat `--list-row-padding-x`; baris & header tidak bisa
  drift. Jangan `px-3` langsung di header/row.
- **Sel vertikal `items-center`**, bukan `items-baseline` — teks dengan ukuran
  berbeda (`text-base-medium` vs `text-p-sm`) terlihat melayang kalau di-baseline.
- **Nama + pelengkap** (kode/email) dalam satu flex `gap-2`: nama
  `text-base-medium text-ink-gray-8`, pelengkap `<code class="shrink-0 text-p-xs text-ink-gray-5">`
  atau `text-p-sm text-ink-gray-5`. Truncate keduanya.
- **Aksi baris = satu ghost icon-only `<Button>`** (`variant="ghost" theme="gray"`,
  `:label` wajib untuk a11y, icon `lucide-pencil` / `lucide-more-horizontal`).
  Badge status dan tombol aksi bisa satu sel (pola labba) atau dipisah kolom —
  pilih satu per page, jangan campur.
- **Badge**: `variant="subtle"` — aktif `green`, nonaktif `gray`; `appRole` admin
  `blue`, user `gray`.
- **Grid `columns`**: `base` harus menampung **semua sel yang tampil** di mobile
  (sel yang `max-md:hidden` tidak dihitung). Jumlah track = jumlah sel visible.
  `md` menyertakan sel yang tampil mulai breakpoint `md`.
- **`list-row-px-3` + row-height 32** untuk list padat admin; jangan icon-size
  lebih besar dari `size-8` di sel baris.
- Chain `loading → error → empty → List` dan gate `v-else` = kontrak data —
  lihat skill **`wiring`** §7a. Polish hanya memegang tampilannya.

## 3. Drift checklist (❌ → ✅)

| ❌ Anti-pattern | ✅ Kanon |
|---|---|
| native `<button>` / `<input>` / `<select>` / `<textarea>` / `<label>` interaktif | komponen frappe — lihat Aturan #0 |
| `aria-label` attr di `<Button>` | prop `label` (attr ditimpa `undefined`) |
| `rounded`, `rounded-sm/md/lg/xl/2xl` | `rounded-1…8` |
| `text-h1`…`text-h6` (tak ada di preset) | `text-<size>` / `text-<size>-<weight>` |
| `text-base font-medium` / `font-semibold` lepas | token gabung `text-base-medium` |
| weight `black` | di-drop dari library — jangan tulis |
| teks paragraf pakai `text-<size>` (LH 1.35) | `text-p-<size>` (LH 1.5–1.6) |
| `focus:ring-2` / `focus-visible:ring` per komponen | andalkan global outline; retheme via `focus-ring-<color>` |
| `toast.success('x', { duration: 5 })` | `{ duration: 5000 }` (default 4000) |
| `<Dialog v-model="show">` | `<Dialog v-model:open="show">` |
| `DialogAction.onClick: () => (x.open = false)` (return nilai) | block body → return `void` |
| `<label>` manual di sekitar input | props `label` / `description` / `error` / `required` |
| `placement` (selection/popover) | `side` + `align` |
| `{ group, items }` (menu) | `{ group, options }` |
| `icon: { name: 'trash-2', theme: 'red' }` (config blob) | `icon: 'lucide-trash-2'` (string) |
| `Popover` `#trigger` + `@click="toggle"` | `#trigger` as-child, tanpa `@click` |
| `triggerClass` / `popoverClass` (class-injection) | slot + hook `data-slot="…"` |
| warna arbitrer `text-[#...]` padahal ada token | ramp (`text-ink-*`, `bg-surface-*`, `border-outline-*`) |
| `` `lucide-${x}` `` (template literal) | literal string atau whitelist |
| `ListFoot` terpisah dari `List` oleh `space-y-4` (pagination mengambang, ada ruang kosong) | bungkus `List` + `ListFoot` di **satu `<div>` polos**; foot `mt-1` |
| `items-baseline` di sel list (teks melayang) | `items-center` |
| sel `max-md:hidden` tapi `columns.base` masih menghitungnya (grid pecah di mobile) | jumlah track `base` = jumlah sel visible |
| `px-3` manual di `ListHead`/`ListRow` | `list-row-px-3` di `<List>` |
| loading list dengan card wrapper | `ListState` — Spinner `flex justify-center py-10` tanpa card |
| `Card` / `ListView` / `Input` / `Autocomplete` (tidak ada di rc.2) | komponen yang memang ada — cek `types.ts` |

---

## 4. Verifikasi visual

1. Jalankan `yarn dev` (`:5173`) di `frontend/`.
2. Cek dark mode juga — token semantic sudah theme-aware, jadi cukup cek
   `data-theme` dan pastikan teks tetap terbaca.
3. Untuk nilai yang presisi (letter-spacing, border-radius), pakai
   `getComputedStyle()` di DevTools — lebih akurat dari screenshot.

---

## Referensi

- Token: `frontend/node_modules/frappe-ui/tailwind/tokens/{typography,radius,effects,colors}.js`
- Utilitas Tailwind: `frontend/node_modules/frappe-ui/tailwind/plugin.js`
- Kontrak komponen: `frontend/node_modules/frappe-ui/src/components/<Name>/types.ts`
- Kode acuan repo: `frontend/src/features/auth/views/LoginView.vue` (form +
  layout), `frontend/src/features/dashboard/views/DashboardView.vue` (panel +
  badge), `frontend/src/app/AppShell.vue` (shell, sidebar, dropdown menu),
  `frontend/src/features/account/views/UsersView.vue` + `frontend/src/shared/components/ListState.vue` (list kanonik).
- Skill lain: `.claude/skills/wiring/SKILL.md`.
