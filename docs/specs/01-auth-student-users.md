# 01 — Auth (Staff & Student) and User Admin

> Parent: [`00-master-overview.md`](00-master-overview.md)
> Scope: `ab_user`, `user_profile`, `ab_role`/`ab_user_role`, staff auth (`/api/v1/auth`), student auth (`/api/v1/student/auth`), user admin (`/api/v1/users`), role system.

---

## 1. Entity & Tables

### 1.1 `ab_user`

| Column | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK | autoincrement |
| `first_name` | VARCHAR(64) NOT NULL | from `full_name`/`name` (split maxsplit=1 → first part) |
| `last_name` | VARCHAR(64) NOT NULL | remainder of the split (can be `""`) |
| `username` | VARCHAR(64) UNIQUE NOT NULL | staff register/admin-create: **= email**; student: free input |
| `password` | VARCHAR(256) | `generate_password_hash` (Werkzeug default) |
| `active` | BOOLEAN | register/create `True`; student soft delete sets it `False` |
| `email` | VARCHAR(320) UNIQUE NOT NULL | always `strip().lower()` |
| `last_login`, `login_count`, `fail_login_count` | — | managed by FAB (read as `lastLogin` in the payload) |
| `created_on`, `changed_on`, `created_by_fk`, `changed_by_fk` | — | FAB columns |

### 1.2 `user_profile`

| Column | Type | Notes |
|-------|------|-------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER UNIQUE NOT NULL → `ab_user.id` CASCADE | 1:1 relation |
| `full_name` | VARCHAR(255) NOT NULL default `''` | |
| `subscription_tier` | VARCHAR(20) NOT NULL default `'community'` | not used by other features |
| `subscription_expires_at` | DATETIME nullable | unused |
| `app_role` | VARCHAR(20) NOT NULL default `'user'` | **source of the backend RBAC gate**: `admin`/`moderator`/`course_creator`/`user` |

The property `current_user.app_role` is patched from this row (fallback `"user"` when there is no profile).

### 1.3 `ab_role` / `ab_user_role`

`ab_role(id, name UNIQUE)` · `ab_user_role(id, user_id, role_id, UNIQUE(user_id,role_id), FK CASCADE)`.

Roles created idempotently at startup (`ensure_roles`): `Admin`, `Moderator`, `Course Creator`, `Tantangan Bebras Student`. The seeder adds `Batch Evaluator`. Legacy map (used by the user admin DTO & the `?role=` filter): `admin→Admin`, `volunter→Moderator`, `guru→Course Creator` (key lowercased; unknown values are used as-is).

### 1.4 `audit_logs` (summary — details in [`06-supporting.md`](06-supporting.md))

`id`, `timestamp` (default now, index), `user_id` → `ab_user.id` **SET NULL**, `action VARCHAR(50)` index, `resource VARCHAR(100)`, `details JSON`, `ip_address VARCHAR(45)`, `user_agent TEXT`.

---

## 2. Flow: Staff Auth (`/api/v1/auth`)

### 2.1 `POST /register` — rate 5/minute

1. `RegisterIn` validation (Pydantic; first error → 400, format in spec 00 §10):
   - `email`: strip + lower, must contain `@` and `.` after `@` → `email_invalid_email`.
   - `password`: **min 8** + check order: uppercase → lowercase → digit → special char (`!@#$%^&*()_+-=[]{}|;:,.<>?`) → `password_password_must_contain_uppercase` / `_lowercase` / `_digit` / `_special_character`; length → `password_must_be_at_least_8_characters`.
   - `full_name`: min 1 → `full_name_required`.
2. `AuthService.register({email, password, fullName})`:
   - email already exists → `ValueError("email_already_registered")` → **409** `email_already_registered` (message is hardcoded, the actual reason is ignored), audit `register_failure` details `{"email","reason":"email_exists"}`.
   - split `full_name` → `first_name` = first word, `last_name` = remainder (or `""`).
   - insert `User(username=email, email=email, active=True, password=hash)` **without a FAB role** + `UserProfile(full_name, subscription_tier="community", app_role="user")`.
   - `IntegrityError` → rollback → 409 same.
3. Success: `login_user(remember=True)` → audit `register_success` → commit → **201** `UserOut`.

### 2.2 `POST /login` — rate 5/minute

1. `LoginIn` (email strip+lower, password free) → 400 `email_required` etc.
2. `authenticate`: `find_by_email` → not found → `None`; `check_password_hash` fails → `None`. **`user.active` is NOT checked** (an inactive staff account can still log in — see hazard 00 §14.11).
3. Failure → audit `login_failure` (`reason:"invalid_credentials"`) → **401** `invalid_credentials`.
4. Success → `login_user(remember=True)` → audit `login_success` → **200** `UserOut`.

### 2.3 `POST /logout` — rate 10/minute

Not logged in → 401 `unauthorized`. `logout_user()` → audit `logout` → **200** `{"message":"logged_out"}` + delete the `remember_token` cookie.

### 2.4 `GET /me`

401 if not logged in; **200** `UserOut`.

### 2.5 `UserOut` shape (camelCase)

`{ id, email, fullName, subscriptionTier, subscriptionExpiresAt (raw isoformat|None), appRole, roles[] (FAB role names), isActive, createdOn (raw isoformat|None) }`

> Timestamps in `UserOut` are **without timezone** (unlike the Tantangan Bebras presenters which add +00:00) — a porting decision.

---

## 3. Flow: Student Auth (`/api/v1/student/auth`)

### 3.1 `GET /login` (branding, public, no auth check) — 200

`{ title: "Tantangan Bebras", subtitle: "Student Login", description: "Sign in to take the Bebras Computational Thinking Challenge according to your category (Cub / Scout / Rover).", register_url: "/student-register", password_min_length: 6, category_options: ["cub","scout","rover"] }`

### 3.2 `POST /register` — public, rate 5/minute

1. `StudentRegister`: `firstName`/`lastName` 1..80; `email` valid + normalized; `username` 3..80; `password` **min 6, no strength rules**; `category` enum; `school ≤140`, `city ≤80`, `country ≤80` default `"Indonesia"`.
2. Service:
   - `username.strip()` duplicate → 409 `username_already_registered` (audit `student_register_failure`, `details.reason` = the message).
   - `email.strip().lower()` duplicate → 409 `email_already_registered`.
   - insert `User(first/last strip(), active=True)` + attach the `Tantangan Bebras Student` role (if missing → `_ensure_student_role()` creates it then flushes).
   - `IntegrityError` → rollback → 409 `username_or_email_taken`.
   - insert `Student(category, school, city, country, **status = "Inactive" hard-coded**)` → commit.
3. Success: `login_user(remember=True)` → audit `student_register_success` → **201** `{ user: {id, username, email, firstName, lastName, isActive}, student: StudentOut }`.

### 3.3 `POST /login` — public, rate 10/minute

`authenticate(username, password)` fails (**all → 401 `invalid_credentials`** + audit `student_login_failure`) when any of:
1. no `User` with `username.strip()`;
2. `user.active == False`;
3. wrong password;
4. a `student` row exists and `student.disabled == True`.

Success → `login_user(remember=True)` → audit `student_login_success` → **200** `{ user: _user_payload, student: StudentOut|null }` (`student` can be `null` when a user with the student role has no discriminator row).

`_user_payload` (all `student/auth` endpoints): `{ id, username, email, firstName, lastName, isActive }`.

### 3.4 `POST /logout` — rate 10/minute

401 if not logged in → `logout_user()` → audit `student_logout` → **200** `{"message":"logged_out"}` — does **not** delete the `remember_token` cookie (unlike staff logout).

### 3.5 `GET /me` → **200** `{ user, student|null }`.

---

## 4. Flow: User Admin (`/api/v1/users`)

**Gate:** every endpoint except `role-list` requires login + `_is_admin()` = `app_role ∈ {admin, moderator, course_creator}` → 401 `unauthorized` / 403 `forbidden`. (See 00 §6.3 — the gate reads `app_role`, not the FAB role name.)

### 4.1 DTO

`UserCreateIn`: `name` 1..255 required (`name_required`); `email` required, valid, strip+lower (`email_invalid_email`); `password` min 6 (`password_must_be_at_least_6_characters`); `role` required — after `LEGACY_ROLE_MAP` it must be ∈ `Admin|Moderator|Course Creator` else `role_role_must_be_admin_moderator_or_course_creator` (`"volunter"` is accepted → `Moderator`).
`UserUpdateIn`: all optional, `extra="ignore"`, empty model validator → `value_no_fields_to_update`.

### 4.2 `GET /` (list)

`limit` default 100 (1..200), `offset ≥0` (bad → 400 `limit_or_offset_invalid`). Query: `?role=` (lowered + legacy map then match `Role.name`; an unknown value is used literally → generally an empty result), `?q=` ilike over `username/email/first_name/last_name`. Order `id DESC`. → **200** `{ items: [_user_payload…] }` (**no `total`**).

### 4.3 `GET /role-list` — **login check only** → **200** `{ roles: ["Admin","Moderator","Course Creator"] }`.

### 4.4 `POST /` — rate 10/minute

1. DTO validation → 400.
2. `username = email` (legacy). Pre-check `User.username == username` already exists → **409** `email_already_registered` (the message says email, the actual check is username).
3. split `name` → first/last; `active=True`; hash the password.
4. `find_role(role)` → if found `user.roles=[role]`; **if not found, the role is silently skipped**.
5. `IntegrityError` → rollback → **409** `username_or_email_taken`.
6. commit → audit `user_admin_created` `details={"role","email"}` → commit → **201** `_user_payload`.

### 4.5 `GET /<id>`

Missing → **404** `user_not_found`. Fetch `Student` optionally → **200** `_user_payload` + key `student` when present.

### 4.6 `PATCH /<id>` — rate 20/minute

Apply per key (only those sent):
- `name` → split into `first_name`/`last_name`.
- `email` → set `email` **and `username = email`** (legacy sync).
- `password` truthy → rehash.
- `role` → `find_role` → replace `user.roles=[role]`; an unknown role is **ignored**; removing all roles is impossible.
- commit → audit `user_admin_updated` `details.changed` = sorted keys → commit → **200** `_user_payload`.

### 4.7 `DELETE /<id>` — rate 10/minute

Missing → 404. **Hard delete** `session.delete(user)` → commit → audit `user_admin_deleted` → commit → **204**.
⚠ Child `student`/`user_profile` rows are not handled → FK error risk on non-SQLite backends (hazard 00 §14.11).

### 4.8 `_user_payload` shape

`{ id, username, email, firstName, lastName, isActive, roles[], createdAt (_iso_utc), lastLogin (_iso_utc), student?: StudentOut }`

---

## 5. Role & app_role Rules

| Attribute | Created by | Read by | Values |
|---|---|---|---|
| FAB role (`ab_user_role`) | `ensure_roles` (startup), student register (`Tantangan Bebras Student`), user admin create/update, seeder | `UserOut.roles`, UI flags (`Admin`→isAdmin, `Tantangan Bebras Student`→isStudent), the `?role=` filter | `Admin`, `Moderator`, `Course Creator`, `Tantangan Bebras Student`, `Batch Evaluator` |
| `app_role` (`user_profile`) | **only** `AuthService.register` → `"user"`; the seeder sets `admin`/`moderator`/`course_creator` | `require_role`, `require_owner_or_role`, `_is_admin`, the practice role dispatch | `admin`, `moderator`, `course_creator`, `user` |

**Porting implication:** a user created via `POST /users` with role `Admin` still has `app_role="user"` → passes the UI (`roles[]`) but is **rejected** by `_is_admin()` (403). The seeder is the only path that sets `app_role` correctly. Decide: bridge the two (FAB role → app_role) or use a single source.

---

## 6. Error Catalog (this domain)

| Code | message |
|------|---------|
| 400 | `email_required`, `email_invalid_email`, `password_password_must_contain_uppercase/_lowercase/_digit/_special_character`, `password_must_be_at_least_8_characters`, `full_name_required` | staff register |
| 400 | `password_must_be_at_least_6_characters`, `category_category_must_be_cub_scout_or_rover`, `username_must_be_at_least_3_characters`, `firstName_required` | student register/create |
| 400 | `name_required`, `password_must_be_at_least_6_characters`, `role_role_must_be_admin_moderator_or_course_creator`, `value_no_fields_to_update` | user admin |
| 401 | `unauthorized` | guard |
| 401 | `invalid_credentials` | both logins |
| 403 | `forbidden` | `_is_admin` |
| 404 | `user_not_found` | user admin get/update/delete |
| 409 | `email_already_registered` (staff register & duplicate username in user admin) | duplicate |
| 409 | `username_already_registered`, `email_already_registered`, `username_or_email_taken` | student register / student create |
| 429 | `rate_limit_exceeded` | rate limit |

---

## 7. UI Flow (Vue)

### 7.1 Login — `/login` (staff & student, public, `NoSidebarLayout`)

- A single card with a local mode toggle `mode: 'login' | 'register'`.
- **Login**: Email (`type=email`, required), Password (required), `Sign in` button (label `Signing in…` while submitting, disabled), inline red error `auth.lastError`. Link "No account? Create one" → register mode.
- **Register**: Full name, Email, Password (`minlength=8`, placeholder "min. 8 characters") → `Sign up`/`Create account`. Link "Already have an account? Sign in".
- Submit → `auth.login/register` → success `router.replace(route.query.redirect || '/')`; the failure message comes from the store.
- Accepts **any active account** (staff & student — the role is the differentiator: staff → staff menu, student row → student menu). After a successful login the store revalidates `GET /student/auth/me` (`syncStudentSession`) so the menu is correct immediately, not only after a refresh.
- HTML5 validation only (`required`, `type=email`, `minlength`).

### 7.2 Student login — `/student-login` (public)

Card "Sign In" / "Sign in as a Tantangan Bebras student". Fields **Username** (required, placeholder `budi`), **Password** (required). `Login` button (`:loading="auth.submitting"`). Error `auth.lastError`. Footer "Don't have an account? Register" → `/student-register`. Submit → `auth.studentLogin` → `router.replace({name:'home'})`.

### 7.3 Student register — `/student-register` (public)

Note "The account will be activated by an admin." Form defaults: `category:'cub'`, `country:'Indonesia'`; fields firstName/lastName/email/username/password required, username `minlength=3`, password `minlength=6`; school/city/country optional; category select literal `cub|scout|rover`. Submit → `auth.studentRegister` → `/home`. Footer → `/student-login`.

### 7.4 Auth store (`stores/auth.ts`)

In-memory state (cleared on refresh): `user`, `student`, `lastError`, `submitting`, `isAuthenticated = !!user`.
`revalidate()` (called by the guard): `GET /auth/me` → ok: set user + `session.setUser(roles)`; failure (anything) → `GET /student/auth/me` → ok: set student + roles `['Tantangan Bebras Student']`; 401 → clear; any other error → `console.warn`.

### 7.5 User admin list — `/users` (`users`)

- Header: breadcrumb "User Admin" + an **Add User** button → `users-new`.
- Toolbar: search (client-side: matches `firstName+lastName`, `email`, lowercase-includes `username`) + a status select `All statuses ''/Active 'true'/Inactive 'false'` (client-side; the list is loaded without params).
- Load `GET /users`; states: loading "Loading users…" / error Alert+Retry / empty (box + "Add User") / ListView.
- Columns: Name · Email · Role (blue badge per `roles[]` entry) · Status (badge `Active` green / `Inactive` gray) · Actions (view → detail, edit, delete red).
- Delete: `dialog.danger` "Delete User" → `DELETE /users/{id}` → splice + toast; on error → toast.

### 7.6 User form — `/users/new` (`users-new`), `/users/:id/edit` (`users-edit`)

- Edit: load `GET /users/{id}` → `form.name = "first last"`, `role = roles[0] || 'Moderator'`.
- Fields: Name (required); Email (`disabled` on edit); Password (required on create, `minlength=6`, edit label "(leave empty to keep unchanged)"); Role select default **`Moderator`**.
- Edit submit → `PATCH {name, role, password?}` (email & an empty password are not sent); create → `POST {name, email, password, role}` → `router.push('/users')`; on failure → inline `error`.

### 7.7 User detail — `/users/:id` (`users-detail`)

- Header card: name + status badge, an email row, `@username`, role badges.
- **Account** card: `User ID #id`, Created (`toLocaleString('id-ID')`), Last Login ("Never" when null), Status.
- **Student Data** card (only `v-if user.student`): a "Student Account" badge, Student ID, Category (`CATEGORY_LABELS`), a Status badge (green when `Active` else orange), optional school/city/country rows.
- Actions: **Edit** → the form; **Reset Password** → `dialog.prompt` password field (`validate`: min 6) → `PATCH {password}` + toast; **Delete** → `dialog.danger` → `DELETE` → toast + `router.replace('users')`.

### 7.8 Guard & session sync

- Router: `meta.public` passes; login required → revalidate → redirect `{name:'login', query:{redirect}}` (the staff **login**, even for student routes). `meta.role` is not enforced.
- Login via `/login` → `session.setUser({roles from backend})`; via student → `roles:['Tantangan Bebras Student']` + `studentCategory`.
- Logout (UserDropdown): if `session.isStudent` → `auth.studentLogout()` else `auth.logout()` → `session.setUser(null)` → `router.replace({name:'login'})`.
