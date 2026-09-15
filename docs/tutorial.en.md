# Tutorial

🌐 [English](tutorial.en.md) | [中文](tutorial.md) | [한국어](tutorial.ko.md)

This tutorial walks through a complete example — from installing the plugin to closing out a requirement.

> Example scenario: implementing "User Points Rule Management" for a backend project.

---

## 1. Installation & initialization

> **Two-step launch**: After installing the plugin, every time you open a Claude Code session, the plugin detects whether the repo is initialized and whether a branch strategy is configured. If either is missing, a guidance message is printed at the start of the session. Complete the two steps below and the message disappears:
>
> 1. `/rd:init <project-name>` — initialize the requirements project
> 2. `/rd:branch init` — configure the branch strategy
>
> After that, run `/rd:new` to create your first requirement.

### 1.1 Install the plugin

```bash
# 1. Add the plugin repo as a marketplace
claude plugins marketplace add https://github.com/zhouhao4221/devflow-claude

# 2. Install the plugin from the marketplace
claude plugins install rd@devflow

# Verify installation
claude plugins list
```

### 1.2 Initialize the requirements project

In the project root, start Claude Code and run:

```
/rd:init my-saas
```

This will:
- Create the requirements directory `docs/requirements/` (`active/`, `completed/`, `modules/`, `templates/`; the location can be adjusted via `requirementsDir`)
- Generate the PRD template `docs/requirements/PRD.md`
- Record the project name, role (`primary`), and requirements directory in `.devflow/settings.json` (shared with the team, checked into Git)

The requirements docs live in a single copy in this repo — writes take effect immediately, with no cache and no sync.

### 1.3 CLAUDE.md architecture description

During init, the plugin checks whether your project CLAUDE.md contains architecture info. If missing, it prompts you to pick a preset template:

```
📋 Pick a project type to generate a CLAUDE.md snippet:

  1. Go backend (Gin + GORM layered architecture)
  2. Java backend (Spring Boot layered architecture)
  3. Frontend project (React/Vue + TypeScript)
  4. Custom (blank template, fill in manually)
  5. Skip
```

The snippet is appended to your project CLAUDE.md and covers tech stack, layered architecture table, coding conventions, testing conventions, etc. `/rd:dev` and `/rd:test` rely on this info to generate plans and locate test files.

> **Edit later**: just edit the "Project Architecture" section of your project CLAUDE.md.

### 1.4 Configure branch strategy (strongly recommended)

```
/rd:branch init
```

> While unconfigured, the session-start banner keeps reminding you; once configured, the reminder disappears. You can still skip configuration — defaults apply (hardcoded `feat/` / `fix/` prefixes, no auto PR).

Pick your team's branch strategy:
- **GitHub Flow** (recommended): branch off `main`, merge back to `main`
- **Git Flow**: feature branches off `develop`, merge back to `develop`
- **Trunk-Based**: short-lived branches, trunk development

Then pick your hosting type:
- **GitHub**: `/rd:pr` suggests the `gh pr create` command
- **Gitea**: `/rd:pr` calls the Gitea REST API to create the PR
- **Other**: only prints `git merge` instructions

After configuration, `/rd:dev`, `/rd:commit`, `/rd:done`, `/rd:pr` all follow the policy.

### 1.5 Reinitialize

Backfill missing files on an existing project (non-destructive):

```
/rd:init my-saas --reinit
```

Use cases:
- Pick up new template files after a plugin upgrade
- Backfill missing directories (e.g. `modules/`, `templates/`)
- Redo the CLAUDE.md architecture prompt
- Recover a deleted `PRD.md` or module doc

### 1.6 Upgrading from v2

Starting in v3, configuration moved from `.claude/settings*.json` to `.devflow/`, and the global cache `~/.claude-requirements/` was removed. On an existing project, after upgrading the plugin, run:

```
/rd:migrate
```

- `requirementProject` / `requirementRole` / `requirementsDir` / `branchStrategy` move to `.devflow/settings.json`, and `giteaToken` moves to `.devflow/settings.local.json`
- Claude Code's own hooks / permissions stay in `.claude/settings.json`
- Read-only repos need to rebind: `/rd:use <primary-repo-path>`
- Once you've confirmed the primary repo's requirements docs are intact, you can manually delete `~/.claude-requirements/projects/<project-name>/`

> At session start, if DevFlow config is still detected under `.claude/`, you'll be prompted to run the migration.

### 1.7 Sync templates (optional)

If the plugin ships new templates:

```
/rd:update-template
```

### 1.8 Configure the Gitea token (required for Gitea repos)

If you chose Gitea in `/rd:branch init`, a token is required for automated PR creation.

**Create the token:**

1. Log into Gitea → avatar (top right) → **Settings**
2. Left menu → **Applications**
3. "Manage Access Tokens" → enter a name (e.g., `claude-pr`)
4. Choose scopes:

| Category | Scope | Required | Notes |
|----------|-------|----------|-------|
| issue | read/write | ✅ | PRs are issues under the hood; needed for create/query |
| repository | read/write | ✅ | Read repo info, list branches, push code |
| user | read | optional | Validate token |

5. Click **Generate Token** → copy & save (shown only once)

**Configure the token:**

`/rd:branch init` already wrote strategy fields like `repoType` and `giteaUrl` into `branchStrategy` in `.devflow/settings.json`. The token is written separately, at the **top level** of the project's `.devflow/settings.local.json` (not inside `branchStrategy`):

```json
{
  "giteaToken": "your-token-here"
}
```

> **Security**: `.devflow/settings.local.json` must not be committed to Git — make sure it is in `.gitignore`.

**Verify:**

```bash
curl -s -H "Authorization: token your-token-here" \
  https://your-gitea.com/api/v1/user
```

If user info is returned, the token works.

---

## 2. Creating requirements

### 2.1 Formal requirements (REQ)

```
/rd:new User Points Rule Management --type=backend
```

AI walks you section by section:

| Section | Content | What you do |
|---------|---------|-------------|
| I. Description | Background, goals, customer scenarios, value | Describe the business context; AI structures it |
| II. Feature list | Checkable list of features | Confirm scope |
| III. Business rules | Validation, state transitions, permissions | Fill in the details |
| IV. Scenarios | Roles, flows, edge cases | Describe typical flows |
| V. API requirements | Endpoint capabilities, I/O, semantics | Confirm API needs |
| VI. Test points | Scenarios to verify | Note test focus |

Generates `docs/requirements/active/REQ-001-user-points-rule-management.md`.

### 2.2 Quick fixes (QUICK)

For small bugs or small features — a lighter flow:

```
/rd:new-quick Fix points calculation precision loss
```

The QUICK template is shorter: problem statement → plan → verification.

### 2.3 Granularity suggestions

Not sure if the scope is right?

```
/rd:split User points system
```

AI analyzes the granularity and suggests a split (read-only, no doc created).

### 2.4 Create from a Git issue

If your team uses Gitea / GitHub issues as the intake:

```
/rd:new --from-issue=#12           # Formal requirement
/rd:new-quick --from-issue=#5      # Quick fix
/rd:do --from-issue=#42            # No doc; treat issue body as the intent for smart dev
```

**What AI does:**
1. Fetches the issue via the API configured in `branchStrategy.repoType` (Gitea → REST API + `giteaToken`; GitHub → `gh issue view`)
2. Uses the issue title as the default requirement title; the body seeds "Problem & current state"
3. Stores `issue: #N` in the doc's metadata, used for downstream auto-linking

**Prereq for Gitea repos**: `branchStrategy.giteaUrl` and `giteaToken` must be set (see 1.8). AI will **not** guess an HTTPS URL from the SSH remote — it must be configured.

#### Issue ↔ branch/commit auto-linking

When linked to an issue, the whole chain carries the issue number:

| Step | Behavior |
|------|----------|
| `/rd:dev` creates the branch | Appends `-iN` (e.g., `feat/REQ-001-user-points-i12`) |
| `/rd:commit` | Appends `closes #N` in the commit message (PR merge auto-closes the issue) |
| `/rd:done` | Asks whether to close the issue via API |
| `/rd:do --from-issue` | Branch gets `-iN`; on completion, asks to close the issue |

**Lookup priority**: doc's `issue` field > `-iN` suffix in branch name. This way, even a doc-less `/rd:do` lets `commit` and `done` infer the issue number from the branch.

---

## 3. Review flow

> QUICK skips review and can go straight to development.

### 3.1 Submit for review

```
/rd:review
```

Status transitions Draft → In Review.

### 3.2 Review decision

```
/rd:review pass     # Approve → Approved
/rd:review reject   # Reject → back to Draft
```

After rejection, use `/rd:edit` to revise and resubmit.

---

## 4. Development

### 4.1 Start development

```
/rd:dev
```

Flow:

```
Prechecks (REQ must be approved)
    ↓
Branch management (auto-create feat/REQ-001-user-points-rule)
    ↓
Read the project architecture from CLAUDE.md (layer order, directory layout)
    ↓
Load requirement context (sections I–VI)
    ↓
Generate implementation plan (Plan Mode)
    ├── 10.1 Data model
    ├── 10.2 API design (from API section + repo code)
    ├── 10.3 File changes (listed by CLAUDE.md layers)
    └── 10.4 Steps (decomposed by CLAUDE.md layer order)
    ↓
Confirm plan → status: In Development
    ↓
Implement layer by layer per CLAUDE.md
```

### 4.2 Branch management

On the first `/rd:dev`, AI automatically:

1. Checks the working tree is clean (aborts if dirty)
2. Reads branch strategy (if `/rd:branch init` was run)
3. Generates an English branch name from the title and asks you to confirm:
   ```
   Will create dev branch: feat/REQ-001-user-points-rule
   Based on branch: main (from branchStrategy.branchFrom)
   ```
4. On confirm, creates the branch and writes `branch` into the doc

Re-running `/rd:dev` just switches to the recorded branch.

Branch naming (prefixes configurable via strategy):
- REQ → `feat/REQ-XXX-<english-slug>[-iN]`
- QUICK → `fix/QUICK-XXX-<english-slug>[-iN]`
- `/rd:do --from-issue` → `<prefix><slug>-iN` (prefix chosen by AI from intent)
- Hotfix → `hotfix/<english-slug>` (via `/rd:branch hotfix`)
- `-iN`: optional issue suffix (e.g., `-i12`), appended automatically when a Git platform issue is linked (see 2.4)

### 4.2.1 Branch strategy commands

```
/rd:branch              # View current strategy and branch status
/rd:branch init         # Interactively configure branch strategy + repo type
/rd:branch status       # View strategy config and each requirement's branch state
/rd:branch hotfix desc  # Create a hotfix branch off main
```

### 4.2.2 Create a PR

When development is done:

```
/rd:pr              # Auto-detect the requirement from the current branch
/rd:pr REQ-001      # Create a PR for a specific requirement
```

Based on the repo type from `/rd:branch init`:
- **Gitea**: calls the Gitea REST API (needs `giteaToken`, see 1.8)
- **GitHub**: uses `gh` CLI
- **Other**: pushes the branch and prints merge instructions

Git Flow hotfix branches get two PRs (→ main + → develop).

### 4.2.3 Review & merge a PR

Use AI review and merge:

```
/rd:pr status              # PR status
/rd:pr review       # AI code review
/rd:pr merge        # Merge the PR
```

**Review flow:**
1. AI fetches the PR diff and reviews file by file (correctness, security, conventions, requirement match)
2. Findings are tiered: 🔴 blocker (must fix), 🟡 suggestion, 🔵 info
3. The review is auto-submitted as a PR comment (visible on Gitea/GitHub web)
4. No blockers → `merge` allowed

**Merge method**: read from `branchStrategy.mergeMethod` (default `merge`); supports `merge` / `squash` / `rebase`.

### 4.2.4 Smart development (`/rd:do`)

For optimizations, refactors, upgrades — no requirement doc needed:

```
/rd:do Optimize order query performance
/rd:do Refactor the user service layer
/rd:do Upgrade Go to 1.23
/rd:do Unify error code formatting
```

AI automatically:
1. **Analyzes intent** — type (optimize/refactor/upgrade/convention/small feature/fix) and scale
2. **Searches the code** — locates relevant files and drafts changes
3. **Confirms the plan** — on confirm, creates a branch (`improve/` / `feat/` / `fix/` chosen by type)
4. **Applies changes** — edits code per the plan

For larger scope, suggests switching to `/rd:new-quick` or `/rd:new`.

**Difference vs `/rd:fix`:**
- `/rd:fix` — dedicated to bug fixing; AI performs root-cause analysis
- `/rd:do` — non-bug (optimize/refactor/upgrade); AI picks the right flow from intent

### 4.3 Continue development

After an interruption, resume:

```
/rd:dev REQ-001
```

Add `--reset` to regenerate the plan:

```
/rd:dev REQ-001 --reset
```

### 4.4 Conventional commits

During development, use the conventional commit helper:

```
/rd:commit
```

AI analyzes the diff and produces a Conventional Commits message:

```
feat: implement points rule CRUD APIs (REQ-001)
```

---

## 5. Testing

### 5.1 Full test

```
/rd:test
```

Runs regression + new feature tests; status → In Testing.

### 5.2 Step-by-step tests

```
/rd:test_regression    # Run existing automated tests, produce a regression report
/rd:test_new           # Create test cases for the new feature (UT/API/E2E)
```

---

## 6. Archival

```
/rd:done
```

Flow:
1. Verify test completion
2. Show summary (features, test points, file stats, timeline)
3. On confirm, archive: `active/REQ-001-*.md` → `completed/`
4. Update PRD index
5. Remind you to merge the dev branch

---

## 7. Browsing & management

### 7.1 Requirements list

```
/rd:req                            # List everything
/rd:req --type=backend             # Filter by type
/rd:req --module=user              # Filter by module
/rd:req --type=frontend --module=user
```

### 7.2 Details

```
/rd:show REQ-001     # Read-only full view
/rd:status REQ-001   # Status + progress
```

### 7.3 Edit

```
/rd:edit REQ-001
```

---

## 8. Module management

Modules are functional-domain docs that help AI understand context.

```
/rd:modules                  # List all modules
/rd:modules new user         # Create the user module doc
/rd:modules show user        # View module details
```

Module docs cover: scope, core features, data model, API overview, key file paths.

---

## 9. PRD management

The PRD is project-level — one per project.

```
/rd:prd                     # PRD overview + section fill rate
/rd:prd-edit                # Edit PRD with AI assistance
/rd:prd-edit Overview       # Edit a specific section
```

The "Requirement Tracking" section of the PRD is auto-maintained:
- `/rd:new` appends a row
- `/rd:done` updates the status and completion date

---

## 10. Versioning

### 10.1 Generate release notes

```
/rd:changelog v1.2.0                          # Auto-detect range
/rd:changelog v1.2.0 --from=v1.1.0 --to=HEAD
```

AI classifies Git commits and generates structured release notes.

### 10.2 Upgrade a quick fix

When a QUICK grows mid-flight:

```
/rd:upgrade QUICK-003
```

---

## 11. Cross-repo collaboration

For projects split across frontend and backend repos.

### Primary repo (backend)

```
# Initialize the project
/rd:init my-saas

# Create and manage requirements normally
/rd:new User Points - Backend --type=backend
```

### Linked repo (frontend)

```
# Bind to the primary repo (pass the local path to the primary repo's root)
/rd:use ../backend

# Read-only access
/rd:req
/rd:show REQ-001

# Develop based on a requirement (reads directly from the primary repo's requirements directory)
/rd:dev REQ-002
```

Linked repos have role `readonly`, with the primary repo's path recorded in `requirementSource.path` in `.devflow/settings.local.json` (a local path, not checked into Git):
- Can view and read requirements
- Can develop based on completed requirements
- Cannot create/edit/transition requirements

### 11.1 Sharing spec docs

The primary repo owns spec docs (data types, API contracts, error codes); read-only repos see them in real time.

**Primary (backend):**

```
/rd:specs new Order data types
/rd:specs edit order-types
/rd:specs
```

**Read-only (frontend):**

```
/rd:specs
/rd:specs show order-types
```

Specs live in the primary repo's `docs/requirements/specs/`; read-only repos read the primary repo's directory directly, with no sync needed. After the backend edits, the frontend sees the latest on next view.

Typical uses:
- Backend defines data types → frontend consumes field definitions
- Shared error codes → implemented on both sides
- API contracts → keep front/back in lockstep

---

## 12. Full flow diagram

```
                  Create requirement
                /rd:new <title>
                      │
                      ▼
               ┌─────────────┐
               │ 📝 Draft    │ ← /rd:edit
               └──────┬──────┘
                      │ /rd:review
                      ▼
               ┌─────────────┐
               │ 👀 In Review│
               └──────┬──────┘
                      │ /rd:review pass
                      ▼
               ┌─────────────┐
               │ ✅ Approved │
               └──────┬──────┘
                      │ /rd:dev (auto branch)
                      ▼
               ┌─────────────┐
               │ 🔨 In Dev   │ ← /rd:commit
               │             │ ← /rd:pr
               │             │ ← /rd:pr review
               │             │ ← /rd:pr merge
               └──────┬──────┘
                      │ /rd:test
                      ▼
               ┌─────────────┐
               │ 🧪 In Test  │
               └──────┬──────┘
                      │ /rd:done (merge reminder)
                      ▼
               ┌─────────────┐
               │ 🎉 Done     │ → archived to completed/
               └─────────────┘
```

---

## 13. Natural language & auto mode

### 13.1 Natural-language commands

No need to memorize slash commands — describe your intent in plain language and the plugin auto-maps it.

**Requirement docs**

```
create a requirement: user points management   → /rd:new user points management
new backend requirement: order export           → /rd:new order export --type=backend
edit REQ-025, add export                        → /rd:edit REQ-025
```

**Fixes & development (no doc)**

```
fix the login timeout bug                       → /rd:fix login timeout
fix bug #42                                     → /rd:fix --from-issue=#42
optimize order query performance                → /rd:do optimize order query performance
refactor the user service layer                 → /rd:do refactor user service layer
upgrade Go to 1.23                              → /rd:do upgrade Go to 1.23
quick change to the pagination default          → /rd:new-quick pagination default
```

**State transitions** (ID required)

```
start developing 025                            → /rd:dev REQ-025
start testing 025                               → /rd:test REQ-025
025 approved / approve 025                      → /rd:review pass
025 rejected                                    → /rd:review reject
done 025 / close 025                            → /rd:done REQ-025
```

**Versioning & PR**

```
commit                                          → /rd:commit
create PR / open PR                             → /rd:pr
review PR                                       → /rd:pr review
pull PR comments                                → /rd:pr comments
merge PR                                        → /rd:pr merge
```

**Paste a Git platform URL** (auto-detect issue / PR)

```
fix owner/repo/issues/169                       → /rd:fix --from-issue=#169
create a requirement from owner/repo/issues/12  → /rd:new --from-issue=#12
review owner/repo/pulls/158                     → /rd:pr review (switch to PR branch first)
```

Pasting a URL without a verb shows a menu to pick the action.

**ID parsing rules**

| Input | Parsed |
|-------|--------|
| `REQ-025` / `REQ025` | REQ-025 |
| `QUICK-003` / `QUICK003` | QUICK-003 |
| Digits `025` / `25` | REQ-025 (zero-padded to 3 digits) |
| `#42` / `issue 42` | `--from-issue=#42` |

**Does NOT trigger**

- Query / display: "show me 025" routes to `/rd:show`
- Discussion / questions: "how do we fix this bug?", "should we refactor?"
- Missing required info: "edit requirement" without ID, "optimize" with no object, "done" with no ID
- Messages starting with a slash command (`/rd:`, `/pm:`, `/api:`)
- URLs pointing to other repos (mismatches `git remote`)

### 13.2 One-shot fix (`--auto`)

`/rd:fix --auto` skips every confirmation and chains commit → push → PR.

> **Preamble**: the rd plugin's confirmations are **off by default** — all Write/Edit/Bash calls go through without prompting. Only users who have told Claude (in natural language) to enable commit confirmation — which makes Claude create `.claude/.req-confirm-commit` and save a feedback memory — see native dialogs before `git commit` / `mv` / `rm` on REQ files; for them, `--auto` drops a `.claude/.req-auto` marker so the hook lets those through. **Even with the default setting, `--auto` still helps** — it skips the command-level text prompts (fix-plan confirm, type picker, close-issue question, etc.) and chains the follow-up steps automatically.

**How to trigger**

```
/rd:fix login timeout --auto                    # Explicit
fix Excel export encoding, no confirm needed     # Natural language
one-shot fix the login timeout                   # Natural language
just fix it and open a PR                        # Natural language
auto-fix #42                                     # Natural language + issue
```

Natural-language triggers: `one-shot fix` / `auto fix` / `just fix and open a PR` / `no confirm` / `don't ask me` / `run through` / equivalents in Chinese.

**Automatically skipped**

| Confirmation | How it's skipped |
|--------------|------------------|
| Fix plan confirmation | Built into the command |
| Native confirm dialog before `git commit` | Off by default; if you opted in via natural language (so `.claude/.req-confirm-commit` exists), the `.claude/.req-auto` marker lets the hook through |
| `/rd:commit` interactive type picker | AI infers "fix" |
| `--from-issue` close-issue question | Defaults to close |
| `/rd:pr` post-create branch cleanup question | Defaults to keep |
| Manually chaining commit → push → PR | Done automatically |

**Cannot be skipped** (Claude Code harness — must be set locally)

- First-time Bash / Write / Edit tool-permission confirmation
- Plan Mode approval (if Plan Mode is enabled)

**Will NOT be skipped** (safety rails)

- Commits on protected branches (`main` / `master` / `develop`) — switch to a dev branch first
- Actual AI analysis and code changes (core execution, not a confirmation)

**Under the hood**

`--auto` creates a `.claude/.req-auto` marker file on start (mtime 10-minute TTL). With the default setup (no `.claude/.req-confirm-commit` marker) there is no native confirm dialog to begin with, so `.req-auto` is inert. Once a user has asked Claude to enable commit confirmation — creating `.req-confirm-commit` — the hook checks `.req-auto` and lets `git commit` through without prompting while an `--auto` flow is live. The marker is cleaned up at the end of the flow; if the process exits abnormally, the TTL expires and the marker stops allowing passes.

`.claude/.req-auto` is already in `.gitignore` — it won't be committed.

**Typical flow**

```
User: fix the Excel export encoding, no confirm needed
   ↓
AI:   🧠 Recognized: /rd:fix Excel export encoding --auto
      ⚙️ --auto skips: [capability list]
      🔒 Cannot skip: [harness permissions]
      🛑 Won't skip: [protected branches, actual code changes]
      Proceed?
   ↓
Diagnose → edit code → git commit → git push → open PR
```

### 13.3 Other commands that support `--auto`

**`/rd:pr review --auto`** — skip the "upload review comment?" confirmation

By default (without `--auto`), after the AI review completes, the command prints a **condensed preview** of the comment that would be uploaded and waits for `y/n`, so the review doesn't go public unreviewed by you. Passing `--auto` skips the prompt and uploads directly.

```
/rd:pr review               # Show preview → wait for y/n
/rd:pr review --auto        # Upload the condensed comment directly
```

Natural-language triggers: `one-shot review`, `auto review`, `review and submit`, `post the review`, `don't ask me`.

> **Only affects the `review` subcommand's upload prompt.** `/rd:pr merge` post-merge branch cleanup is controlled by `branchStrategy.deleteBranchAfterMerge`; `/rd:pr comments` keeps its "apply changes?" prompt so AI doesn't silently edit code.

---

## Cheat sheet

| Scenario | Command |
|----------|---------|
| Browse requirements | `/rd:req` |
| Create a formal requirement | `/rd:new <title> --type=backend` |
| Quick fix (with doc) | `/rd:new-quick <title>` |
| Lightweight fix (no doc) | `/rd:fix <description>` |
| Smart dev (optimize/refactor) | `/rd:do <description>` |
| Edit | `/rd:edit` |
| Submit for review | `/rd:review` |
| Approve | `/rd:review pass` |
| Start development | `/rd:dev` |
| Commit | `/rd:commit` |
| Create PR | `/rd:pr` |
| AI review | `/rd:pr review` |
| Merge PR | `/rd:pr merge` |
| Run tests | `/rd:test` |
| Archive | `/rd:done` |
| View PRD | `/rd:prd` |
| Generate changelog | `/rd:changelog v1.0.0` |
| Configure branch strategy | `/rd:branch init` |
| Branch status | `/rd:branch status` |
| Hotfix | `/rd:branch hotfix <description>` |
| Reinitialize | `/rd:init my-project --reinit` |
| Upgrading from v2 | `/rd:migrate` |
| View spec doc | `/rd:specs show <name>` |
| Create spec doc | `/rd:specs new <name>` |
