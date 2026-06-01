# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

RCOS IO is an admin/member portal for the Rensselaer Center for Open Source (RCOS). It manages thousands students/semester: enrollments, projects, meetings, attendance, mentors, small groups, and external organizations. Mostly CRUD over a relational DB. Built with Django, plain HTML templates (Bulma CSS), Postgres, and Redis. Hosted on Railway.

## Commands

Dependencies are managed with **uv**. Always run Django via `uv run ./manage.py ...`.

- `docker compose -f dev-docker-compose.yml up -d` — start local Postgres + Redis (required before setup/dev)
- `make setup` — first-time setup: `uv sync`, copy `.env`, migrate, create cache table, create superuser (`admin@example.com` / `admin`), generate + load fixtures
- `make dev` — run dev server (login at `http://127.0.0.1:8000/auth/login/`)
- `make migrate` — `makemigrations` + `migrate`
- `make lint` — `ruff check .` + `ruff format --check .`
- `make lint-fix` — auto-fix + format
- Tests use Django's test runner: `uv run ./manage.py test` (note: `portal/tests.py` is currently empty — there is effectively no test suite yet)
- Regenerate fixtures: `uv run python portal/fixtures/generate.py > portal/fixtures/data.json` (uses Faker)

Deploy to production: `git push origin main:production`.

## Auth & login flow

- Auth is **passwordless via magic link** (`django-magiclink`). There is no password login for normal users. First login auto-creates a `User` (`MAGICLINK_REQUIRE_SIGNUP = False`).
- In local dev, emails are printed to the console (`console.EmailBackend`), so the magic link appears in server logs. In prod, Mailjet via `django-anymail`.
- `AUTH_USER_MODEL = "portal.User"` — custom user model keyed by email.
- Account linking: users connect **Discord** and **GitHub** via OAuth flows (`portal/views/auth.py`, callbacks in `portal/urls.py`).

## Settings & environment

- All config comes from environment variables loaded via `python-dotenv` (`.env`, copied from `.env.example`). `rcos_io/settings.py` reads them with `os.environ[...]` — **missing vars raise KeyError at startup**, so new env vars must be added to `.env` and `.env.example`.
- `DEBUG` is on when `ENV == "development"`. Many behaviors branch on `DEBUG` (debug toolbar, console email, `UserRequiresSetupMixin`/`CheckUserSetup` short-circuit to allow access).
- Sessions are stored in the **cache** (Redis), not the DB. The cache table (`createcachetable`) exists from setup but Redis is the active cache backend.

## Architecture

Single Django app: **`portal`**. The project package `rcos_io` holds settings/urls/celery/wsgi.

### Domain model (`portal/models.py`, ~1700 lines — the core of the app)

All models extend `TimestampedModel`. The data model is **semester-centric**:

- `Semester` — the central time unit. Has deadline fields (`enrollment_deadline`, `project_pitch_deadline`, `project_proposal_deadline`, `mentor_application_deadline`). `Semester.get_active()` and `.is_active` drive most "is this allowed right now" logic. The active semester is cached (see below).
- `User` — custom user. `role` is `RPI` or `EXTERNAL` (RPI = `@rpi.edu`-affiliated). RPI/external distinction gates many features. Per-semester roles (mentor/coordinator/faculty advisor/project lead) live on **`Enrollment`**, NOT on `User`. `User.is_mentor(semester)` etc. delegate to the user's enrollment for that semester.
- `Enrollment` — links a `User` to a `Semester` (and optionally a `Project`). Boolean role flags: `is_project_lead`, `is_mentor`, `is_coordinator`, `is_faculty_advisor`, `is_for_pay`. This is where "what is this person for this semester" is answered.
- `Project` and its lifecycle: `ProjectPitch` → `ProjectProposal` → `ProjectPresentation`, plus `ProjectEnrollmentApplication`, `ProjectRepository`, `ProjectTag`.
- `Meeting` / `MeetingAttendance` / `MeetingAttendanceCode` — attendance is taken via short-lived codes.
- `MentorApplication`, `SmallGroup`, `Organization`, `StatusUpdate`/`StatusUpdateSubmission`, `ShortLink`.

### Permission checks (`portal/checks.py`)

Authorization beyond Django's built-ins is a **composable `Check` class system**, not decorators. Each `Check` declares `dependencies` (other checks that run first), a `fail_reason`, and an optional `fix` (user-facing remediation text). Call `.check(user, semester, project)` → returns a truthy/falsy `CheckResult`, or `.passes(...)` → bool. Composite checks like `CheckUserCanEnroll`, `CheckUserCanCreateProject`, `CheckUserCanPitchProject` chain setup/role/deadline checks. When adding a gated action, compose existing checks rather than re-implementing the logic inline.

### Views (`portal/views/`)

Views are split by domain into modules (`projects.py`, `meetings.py`, `admin.py`, `auth.py`, etc.) and re-registered in `portal/urls.py`. Mix of function views and class-based views.

`portal/views/__init__.py` defines **reusable CBV mixins** that views compose — prefer these over hand-rolling query logic:
- `SemesterFilteredListView` / `SemesterFilteredDetailView` — filter by `?semester=<id>` query param (via `semester_filter_key`), 404 on invalid, optionally default to active semester.
- `OrganizationFilteredListView` — filter by `?organization=<id>`.
- `SearchableListView` — Postgres full-text search via `?search=`, using either `search_fields` (SearchVector) or a precomputed `search_vector_field`.
- `UserRequiresSetupMixin` — gates a view on `user.is_setup` (bypassed when `DEBUG`).
- `load_semesters` — a **context processor** (registered in settings `TEMPLATES`) that injects `semesters` and `active_semester` into every template, read from cache.

### External services (`portal/services/`)

- `discord.py` — Discord REST API wrapper (channels, roles, messages, member sync). Models call into this (e.g. `User.sync_discord`, `Enrollment.sync_discord`).
- `github.py` — GitHub API (GraphQL via `gql`) for repo data and account linking.

Be careful editing these: methods hit live external APIs and are called synchronously from views and model `save()` paths in some cases, and from Celery tasks in others.

### Background tasks (`portal/tasks.py`, `rcos_io/celery.py`)

Celery with Redis as both broker and result backend. Tasks: `delete_discord_channels` (rate-limited bulk delete), `meetings_alert` (Discord notification for meetings missing slides). `django_celery_beat` is present but commented out in `INSTALLED_APPS`.

### Caching

Redis-backed. The semester list and active semester are cached for 24h via `cache.get_or_set` in `load_semesters`. **If you change `Semester` data programmatically, invalidate the `"semesters"` / `"active_semester"` cache keys** or stale data will render across the site.

### Management commands

`portal/management/commands/` — e.g. `delete_unverified_users.py`. Run with `uv run ./manage.py <command>`.

## Conventions

- Ruff is the linter/formatter. Config in `pyproject.toml`: rule sets `E,W,F,I,UP,RUF`; ignores `E501` (line length) and `RUF012`. Run `make lint-fix` before committing.
- Templates live in `portal/templates/` (app) and `templates/` (project-level). Frontend is server-rendered HTML + Bulma; forms use `django-crispy-forms` with the `bulma` template pack.
- Frontend Markdown rendering is sanitized through `django-markdownify` with an allowlisted tag set (see `MARKDOWNIFY` in settings) — don't expand the allowlist without reason.
- Python 3.11 per `pyproject.toml`/`.python-version` (note `runtime.txt` says 3.13 for the Railway runtime).
