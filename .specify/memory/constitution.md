<!--
SYNC IMPACT REPORT
==================
Version change: (unfilled template) → 1.0.0
Rationale: Initial ratification. All placeholder tokens replaced with concrete,
enforceable governance. MAJOR bump to 1.0.0 establishes the baseline.

Modified principles:
  [PRINCIPLE_1_NAME] → I. Privacy & Security First (NON-NEGOTIABLE)
  [PRINCIPLE_2_NAME] → II. Unit Tests Always (NON-NEGOTIABLE)
  [PRINCIPLE_3_NAME] → III. Storage Portability
  [PRINCIPLE_4_NAME] → IV. Modern Python & Clean Code
  [PRINCIPLE_5_NAME] → V. Minimal Scope

Added sections:
  [SECTION_2_NAME] → Technology Constraints
  [SECTION_3_NAME] → Development Workflow & Quality Gates
  Governance (rules populated)

Removed sections: none

Deferred items:
  None. RATIFICATION_DATE set to the date of this initial adoption (2026-08-21);
  the repository predates it (first commit 2026-03-11) but had no ratified
  constitution until now.
-->

# Brokelog Constitution

## Core Principles

### I. Privacy & Security First (NON-NEGOTIABLE)

Brokelog holds personal financial records. That data MUST never leave the user's control.

- Transaction data, account identifiers, and uploaded CSVs MUST NOT be transmitted to any
  third-party service, analytics endpoint, or external API. Local-first is the default and any
  exception requires an explicit, documented, opt-in user decision.
- Secrets, credentials, connection strings, and real financial exports MUST NOT be committed to
  the repository. Configuration comes from environment variables or ignored local files.
- Logs and error responses MUST NOT contain full account numbers, raw CSV rows, or transaction
  descriptions. Error messages report what failed, not the data that failed.
- All external input (uploaded files, request bodies, query parameters) MUST be validated before
  use. Database access MUST use parameterized queries or an ORM — never string-interpolated SQL.
- Once the web interface exists, every route that reads or writes transaction data MUST enforce
  authentication and MUST scope results to the requesting owner.

**Rationale**: A leak here is irreversible and personally damaging. Privacy is a property of the
design, not a feature added later.

### II. Unit Tests Always (NON-NEGOTIABLE)

Every behavior change ships with tests in the same change.

- New modules, parsers, endpoints, and bug fixes MUST have unit tests covering the happy path and
  at least one failure or edge case.
- A bug fix MUST include a test that fails before the fix and passes after it.
- Tests MUST be deterministic and MUST NOT depend on network access, wall-clock time, or a
  developer's local database.
- The full suite MUST pass before any change is merged.

**Rationale**: Sign conventions, date formats, and per-institution CSV quirks are silent failure
modes. Tests are the only practical way to catch a transaction that lands with the wrong sign.

### III. Storage Portability

Persistence goes through a SQL abstraction layer, never through database-specific access.

- SQLite is the default and MUST work with zero configuration.
- The database connection MUST be configurable so another SQL backend (PostgreSQL, MySQL) can be
  substituted without changing application logic.
- Application and route code MUST NOT contain raw vendor-specific SQL or rely on SQLite-only
  behavior. Schema and query construction go through the ORM.
- Schema changes MUST be expressed as reviewable migrations, not manual database edits.

**Rationale**: Personal use starts on a single file; a shared or hosted deployment needs a real
server. Choosing that later must not require a rewrite.

### IV. Modern Python & Clean Code

- Python 3.12+ only. Modern syntax and standard-library features are preferred over back-compat
  shims.
- All function signatures MUST carry type annotations. `mypy --strict` MUST pass.
- `ruff check` MUST pass with no errors and no blanket suppressions; a targeted `# noqa` requires
  an inline reason.
- Functions do one thing and are named for what they do. Duplicated logic is extracted rather than
  copied. Shared behavior lives in a base class or helper, not repeated per implementation.
- Public modules, classes, and non-obvious functions carry docstrings explaining intent, not
  restating the code.

**Rationale**: Static checking and consistent structure are what make a small codebase safe to
change months later.

### V. Minimal Scope

Build the smallest thing that satisfies the requirement.

- Features MUST be driven by a stated need for personal expense tracking. Speculative
  generality — abstractions with a single implementation, configuration nobody sets, layers
  nobody calls — MUST NOT be added.
- New runtime dependencies MUST be justified in the change that introduces them. The standard
  library is the default answer.
- Added complexity MUST be defensible in review; if it cannot be explained, it is removed.

**Rationale**: This is a personal tool. Every unnecessary abstraction is maintenance burden with
no user on the other side of it.

## Technology Constraints

- **Language**: Python 3.12 or later.
- **Storage**: A SQL database accessed through an ORM. SQLite is the default implementation;
  the backend MUST remain swappable per Principle III.
- **Interface**: A REST API is the current surface. A web interface is planned but its stack,
  framework, and design are **not yet defined** and MUST be specified before implementation
  begins. Until then, no web-UI assumptions may be baked into the API layer.
- **Tooling**: `uv` for dependency management, `pytest` for tests, `ruff` for linting,
  `mypy` for type checking. These are the authoritative gates.
- **Data handling**: Financial data stays local. See Principle I.

## Development Workflow & Quality Gates

Every change MUST satisfy all of the following before merge:

1. `uv run pytest` — full suite passes, new behavior is covered.
2. `uv run ruff check src/` — clean.
3. `uv run mypy src/` — clean under strict mode.
4. No secrets, credentials, or real financial data added to the repository.
5. Documentation updated when behavior, format support, or setup steps change.

Work proceeds on a branch and merges via pull request. Review MUST confirm constitutional
compliance, not just correctness — a reviewer who spots an unjustified abstraction, an untested
path, or leaked personal data blocks the change.

## Governance

This constitution supersedes other conventions and preferences. Where a habit, prior pattern, or
convenience conflicts with a principle here, the principle wins.

**Amendment procedure**: Amendments are proposed as a change to this file, with the rationale
stated in the pull request. An amendment takes effect when merged. The Sync Impact Report at the
top of this file MUST be updated in the same change.

**Versioning policy**: Semantic versioning applies to this document.
- **MAJOR** — a principle is removed or redefined in a way that invalidates existing practice.
- **MINOR** — a principle or section is added, or existing guidance is materially expanded.
- **PATCH** — clarification, wording, or typo fixes with no change in meaning.

**Compliance review**: Compliance is verified at pull-request review and enforced by the quality
gates above. Violations are fixed or explicitly waived in writing in the pull request; an
undocumented violation is a blocker. Runtime development guidance lives in `CLAUDE.md`, which
MUST remain consistent with this constitution.

**Version**: 1.0.0 | **Ratified**: 2026-08-21 | **Last Amended**: 2026-08-21
