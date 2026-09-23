# DevFlow

🌐 [English](README.en.md) | [中文](README.md) | [한국어](README.ko.md)

AI-driven software lifecycle management toolkit. Covers requirements analysis, development guidance, testing, project management, and API integration — end-to-end. Built on the Claude Code plugin system.

## Plugins

| Plugin | Description |
|--------|-------------|
| **rd** (R&D) | R&D workflow — requirements, review, development, testing, archival + branch/PR/issue/release (formerly the req plugin) |
| **pm** | Project management helper — weekly/monthly reports, stats, risk scan, plans |
| **api** | API integration — Swagger parsing, field mapping, code generation |
| **diag** | Production diagnostics — read-only SSH log pull, stack trace parsing, code correlation, fix suggestions |

> Each plugin's current version is tracked via `claude plugins list` or `plugins/<plugin>/.claude-plugin/plugin.json` in the repo.
>
> The former `req` plugin has been renamed to `rd` (R&D): if you installed `req@devflow`, uninstall it, install `rd@devflow`, then run `/rd:migrate` in your project to clean up old prefix references.

---

## Installation

> Requires Claude Code v1.0.33 or higher (v2.1+ recommended).

```bash
# Install from GitHub
claude plugins marketplace add https://github.com/zhouhao4221/devflow-claude
claude plugins install rd@devflow    # Requirements management
claude plugins install pm@devflow     # Project management helper
claude plugins install api@devflow    # API integration
claude plugins install diag@devflow   # Production diagnostics
```

```bash
# Plugin management
claude plugins list                   # List installed plugins
claude plugins update rd@devflow     # Update a plugin
claude plugins uninstall rd@devflow  # Uninstall a plugin
```

---

## Model Strategy

Commands and worker subagents run on your current session model; only the most reasoning-heavy steps go to a Fable subagent:

| Layer | Model | What it does |
|-------|-------|--------------|
| Commands | Your session model | Every `/rd:*`, `/pm:*`, `/api:*`, `/diag:*` |
| Worker subagents | Your session model | Locating code, running tests, digesting large diffs, template-driven drafting, editing code per a confirmed plan |
| Thinking subagents | Fable | The implementation plan in `/rd:dev` and `/rd:do`, the root cause and fix plan in `/rd:fix`, small-PR review in `/rd:review`, root-cause analysis in `/diag:diagnose` |

Commands no longer declare a `model` tier: Claude Code's auto mode (the default on Pro / Max / Team) doesn't support Haiku, so a command-level override is ignored; and even when it applies, switching models mid-conversation rebuilds the whole conversation's prompt cache on the new model, which often costs more. To cut cost, switch the whole session with `/model`.

When Fable isn't available (credits used up, not enabled, or not offered by your cloud provider), the session model takes over automatically and the output starts with "⚠️ Fable unavailable". On some plans Fable bills to usage credits, and interactive sessions ask for consent the first time.

Subagents start with a fresh context, so raw output (test logs, large diffs) stays out of the main session.

Each command also pre-approves only the tools it needs via `allowed-tools`; if a read-only command calls a write tool, you still get a permission prompt first.

---

## rd plugin (R&D) — Requirements & development workflow

Covers the full lifecycle from analysis, review, development, testing, to archival.

### Core features

- **Natural-language dispatcher**: describe intent in plain language and auto-map to the right `/rd:*` command (e.g., "fix the login timeout bug" → `/rd:fix`, "start developing 025" → `/rd:dev REQ-025`; pasting an issue/PR URL also works)
- **Auto mode**: `/rd:fix --auto` skips every confirmation and chains commit → push → PR in one shot (a `.claude/.req-auto` marker lets the native git-confirm dialog through)
- **AI-guided requirements analysis**: AI asks questions round by round, then generates a complete document in one shot
- **Full lifecycle**: Draft → In Review → Approved → In Development → In Testing → Done
- **Dual tracks**: formal requirements (REQ) and quick fixes (QUICK)
- **Smart development**: `/rd:do` — describe your intent and AI picks the flow, creates a branch, and drafts the plan
- **Development guidance**: reads your project's layered architecture from CLAUDE.md and guides layer by layer (stack-agnostic)
- **Live doc maintenance during dev**: AI flags deviations and prompts to update the requirement doc
- **Branch management**: GitHub Flow / Git Flow / Trunk-Based
- **Front/back collaboration**: frontend REQ describes interaction, `dev` stage auto-matches backend APIs
- **PR review & merge**: AI code review, auto-submit comments, one-click merge
- **Git issue integration**: `--from-issue=#N` creates a requirement directly from a Gitea/GitHub issue; branches/commits/done auto-link and auto-close
- **Cross-repo sharing**: front/back repos share the same requirement set (single source of truth in the primary repo; readonly repos read directly, no cache, no sync)
- **Conventional commits**: auto-attach the requirement ID
- **Changelog**: generated from Git history

### Quick start

**New projects only need two steps to launch** (the plugin will prompt you at the start of every session — both are required):

```bash
# 1. Initialize the project (creates docs/requirements/, generates PRD, binds the repo)
/rd:init my-project

# 2. Configure branch strategy (GitHub Flow / Git Flow / Trunk-Based + hosting type)
/rd:branch init
```

Then the daily workflow:

```bash
# 3. Create a requirement (AI asks questions → generates doc in one shot)
/rd:new user points system

# 4. Review
/rd:req-review pass

# 5. Develop (AI generates a plan and guides you layer by layer)
/rd:dev

# 6. Test
/rd:test

# 7. Archive
/rd:done
```

### Command reference

#### Requirements

| Command | Description |
|---------|-------------|
| `/rd:req` | List all requirements; supports `--type` and `--module` filters |
| `/rd:new [title]` | Create a formal requirement (AI Q&A → generate doc) |
| `/rd:new-quick [title]` | Create a quick fix (small bug / small feature) |
| `/rd:do <description>` | Smart development (optimize/refactor/upgrade/tweak, no doc) |
| `/rd:fix <description>` | Lightweight fix (bug fix, no doc) |
| `/rd:edit [REQ-XXX]` | Edit a requirement |
| `/rd:show [REQ-XXX]` | Show requirement details (read-only) |
| `/rd:status [REQ-XXX]` | Show requirement status |
| `/rd:req-review [pass\|reject]` | Submit (with AI pre-review) / approve / reject review |
| `/rd:dev [REQ-XXX]` | Start or continue development |
| `/rd:test [REQ-XXX]` | Full test verification |
| `/rd:test_regression` | Run existing automated tests |
| `/rd:test_new` | Create new test cases for a new feature |
| `/rd:done [REQ-XXX]` | Complete and archive |
| `/rd:upgrade <QUICK-XXX>` | Upgrade a quick fix to a formal requirement |
| `/rd:split [description]` | Granularity analysis and split suggestions |

#### PR review & merge

| Command | Description |
|---------|-------------|
| `/rd:pr [REQ-XXX]` | Create PR (auto-detects GitHub / Gitea) |
| `/rd:pr status` | Show PR status |
| `/rd:review` | AI code review, submit comments |
| `/rd:pr comments` | Fetch and list PR comments (read-only) |
| `/rd:review comments` | Apply reviewer comments to the code |
| `/rd:pr merge` | Merge PR (supports merge/squash/rebase) |

#### Document management

| Command | Description |
|---------|-------------|
| `/rd:prd` | PRD status overview |
| `/rd:prd-edit [section]` | Edit PRD |
| `/rd:modules` | List all modules |
| `/rd:specs` | Spec documents (data types, API contracts, etc.) |

#### Versioning & branches

| Command | Description |
|---------|-------------|
| `/rd:commit [message]` | Conventional commit with auto-attached requirement ID |
| `/rd:changelog <version>` | Generate release notes |
| `/rd:branch init` | Configure branch strategy |
| `/rd:branch hotfix [description]` | Create a hotfix branch |

#### Project configuration

| Command | Description |
|---------|-------------|
| `/rd:init <project-name>` | Initialize a project |
| `/rd:use <primary-repo-path>` | Bind the primary repo; sets the current repo to readonly |
| `/rd:projects` | View the current requirement project |
| `/rd:migrate` | Migrate from the v2 layout to `.devflow/` |
| `/rd:update-template` | Sync the latest templates from the plugin |

### Requirement lifecycle

```
Formal (REQ):   Draft → In Review → Approved → In Development → In Testing → Done
Quick fix (QUICK): Draft → In Development → In Testing → Done (only skips review)
```

### Document structure

| Section | Content | Filled by |
|---------|---------|-----------|
| Requirement definition | I–VI (description, feature list, rules, scenarios, data & UX, test points) | AI Q&A → generated in one shot |
| Process log | VII–IX (review, change log, linked info) | Auto-filled by commands |
| Implementation plan | X (data model, API design, file changes, steps) | Generated by `/rd:dev` |

### Cross-repo sharing

```
~/backend/   (primary)  → docs/requirements/  Single source of truth, git-tracked, writes take effect immediately
~/frontend/  (readonly) → Bind with /rd:use ~/backend to read the primary repo's requirements directly; dev auto-matches backend APIs
```

Configuration lives in `.devflow/settings.json` (team-shared, git-tracked) and `.devflow/settings.local.json` (secrets and local paths, not git-tracked). Projects upgrading from v2, or switching from the renamed req plugin to rd, should run `/rd:migrate`.

### AI skills (auto-triggered)

| Skill | Trigger |
|-------|---------|
| `requirement-analyzer` | When creating/editing a requirement — AI Q&A → generate doc |
| `dev-guide` | During development — layered guidance + live doc maintenance |
| `quick-fix-guide` | Quick fixes — fast analysis and plan |
| `test-guide` | Testing stage — regression and new test creation |
| `prd-analyzer` | When editing PRD — assists with each section |
| `code-impact-analyzer` | On requirement change — analyzes code impact |
| `changelog-generator` | Generates release notes |

---

## pm plugin — Project management helper

Extracts project data from PRD, requirement docs, and Git history to generate reports, stats, and plans tailored to different audiences.

- **Read-only**: consumes what rd produces; never mutates requirement docs
- **Works without rd**: Git stats and free-form Q&A still work without requirement data
- **Optional persistence**: every output can be saved to `docs/reports/`

| Command | Description |
|---------|-------------|
| `/pm` | Project dashboard |
| `/pm:weekly` | Weekly report |
| `/pm:monthly` | Monthly report |
| `/pm:milestone <version>` | Milestone/release summary |
| `/pm:stats` | Multi-dimensional stats |
| `/pm:progress` | Project progress (Gantt view) |
| `/pm:plan <topic>` | Plan document (schedule/technical/resource) |
| `/pm:risk` | Risk scan |
| `/pm:standup` | Standup summary |
| `/pm:ask <question>` | Free-form Q&A over project data |

---

## api plugin — API integration

Frontend API integration toolkit with Swagger/OpenAPI parsing, field mapping, and code generation.

| Command | Description |
|---------|-------------|
| `/api:import` | Import a Swagger document |
| `/api:search <keyword>` | Search endpoints |
| `/api:gen` | Generate TypeScript types and request functions |
| `/api:map` | Field mapping analysis |

---

## diag plugin — Production diagnostics

Describe a production error in plain language, and the plugin pulls logs read-only over SSH, parses the stack trace, correlates it with local code, and gives fix suggestions. **Read-only throughout**: SSH host allowlist, command verb allowlist, write-operation blocking, sensitive-input interception, and other guardrail hooks are all enforced, with every SSH command audited to disk.

| Command | Description |
|---------|-------------|
| `/diag:init` | Configure the service inventory (hosts, log paths) |
| `/diag:diagnose <error description>` | Pull logs → parse stack trace → correlate code → fix suggestions |
| `/diag:audit` | Query audit records |

See [plugins/diag/README.md](plugins/diag/README.md) for details.

---

## Tutorial

Full step-by-step tutorial: [docs/tutorial.en.md](docs/tutorial.en.md).

## License

[Apache License 2.0](LICENSE)
