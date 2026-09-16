# DevFlow

🌐 [English](README.en.md) | [中文](README.md) | [한국어](README.ko.md)

AI 기반 소프트웨어 전체 생명 주기 관리 툴킷. 요구사항 분석, 개발 가이드, 테스트, 프로젝트 관리, API 연동까지 전 과정을 커버합니다. Claude Code 플러그인 시스템 위에 구축되었습니다.

## 플러그인

| 플러그인 | 설명 |
|---------|------|
| **rd** (R&D, 연구개발) | 연구개발 워크플로우 — 요구사항 분석·리뷰·개발·테스트·아카이브 + 브랜치/PR/issue/버전 (기존 req 플러그인) |
| **pm** | 프로젝트 관리 도우미 — 주간/월간 리포트, 통계, 리스크 스캔, 기획안 |
| **api** | API 연동 — Swagger 파싱, 필드 매핑, 코드 생성 |
| **diag** | 프로덕션 진단 — 읽기 전용 SSH 로그 수집, 스택 분석, 코드 연결, 수정 제안 |

> 각 플러그인의 현재 버전은 `claude plugins list` 또는 저장소 내 `plugins/<플러그인>/.claude-plugin/plugin.json` 을 기준으로 합니다.
>
> 기존 `req` 플러그인은 `rd`(R&D)로 이름이 변경되었습니다: `req@devflow` 를 설치했다면 제거 후 `rd@devflow` 를 설치하고, 프로젝트에서 `/rd:migrate` 로 기존 접두사 참조를 정리하세요.

---

## 설치

> Claude Code v1.0.33 이상 필요 (v2.1+ 권장).

```bash
# GitHub 에서 설치
claude plugins marketplace add https://github.com/zhouhao4221/devflow-claude
claude plugins install rd@devflow    # 요구사항 관리
claude plugins install pm@devflow     # 프로젝트 관리 도우미
claude plugins install api@devflow    # API 연동
claude plugins install diag@devflow   # 프로덕션 진단
```

```bash
# 플러그인 관리
claude plugins list                   # 설치된 플러그인 목록
claude plugins update rd@devflow     # 플러그인 업데이트
claude plugins uninstall rd@devflow  # 플러그인 제거
```

---

## 스마트 모델 분기

커맨드는 추론 강도에 따라 세 단계로 나뉘며, frontmatter 의 `model` 필드로 선언해 응답 속도와 추론 품질의 균형을 맞춥니다:

| 단계 | 용도 | 대표 커맨드 |
|------|------|-------------|
| **Haiku** | 순수 조회 / 표시 / 설정 / 규칙이 명확한 상태 전환 | `/rd:req`, `/rd:status`, `/rd:show`, `/rd:commit`, `/pm:standup`, `/api:help` |
| **Sonnet** | 데이터 집계 + 문서화 | `/pm:weekly`, `/pm:monthly`, `/pm:stats`, `/pm:risk` |
| **세션 모델**(미지정) | 코드 분석 / 기획안 생성 / 다회차 요구사항 논의 | `/rd:new`, `/rd:dev`, `/rd:fix`, `/rd:do`, `/rd:pr`, `/api:gen`, `/pm:plan` |

개발 계열 커맨드는 코드 위치 파악, 테스트 실행, 대형 diff 압축 등 처리량이 큰 단계를 subagent 에 위임하여 원본 출력이 메인 세션 컨텍스트에 들어가지 않도록 합니다.

각 커맨드는 `allowed-tools`로 필요한 툴만 사전 승인하며, 읽기 전용 커맨드가 쓰기 툴을 호출하면 먼저 권한 확인 창이 뜹니다.

---

## rd 플러그인 (R&D) — 요구사항 & 개발 워크플로우

분석, 리뷰, 개발, 테스트부터 아카이브까지 전체 생명 주기를 커버합니다.

### 핵심 기능

- **자연어 디스패처**: 자연어로 의도를 말하면 `/rd:*` 커맨드에 자동 매핑 (예: "로그인 타임아웃 버그 고쳐" → `/rd:fix`, "025 개발 시작" → `/rd:dev REQ-025`; issue/PR URL 붙여넣기도 지원)
- **원클릭 모드**: `/rd:fix --auto` 로 모든 확인 인터랙션을 건너뛰고 commit → push → PR 까지 자동 연결 (`.claude/.req-auto` 마커로 네이티브 git 확인 다이얼로그 통과)
- **AI 문답형 요구사항 분석**: AI 가 라운드별로 질문하여 정보를 수집한 뒤 한 번에 완성된 문서를 생성
- **전체 생명 주기**: 초안 → 리뷰 대기 → 리뷰 통과 → 개발 중 → 테스트 중 → 완료
- **듀얼 트랙**: 정식 요구사항 (REQ) 과 빠른 수정 (QUICK) 두 가지 워크플로우
- **스마트 개발**: `/rd:do` — 의도만 설명하면 AI 가 흐름을 선택하고 브랜치를 만들고 기획안을 작성
- **개발 가이드**: 프로젝트 CLAUDE.md 의 계층 아키텍처를 읽어 계층별로 안내 (스택 무관)
- **개발 중 문서 유지보수**: AI 가 편차를 감지하면 요구사항 문서 업데이트를 제안
- **브랜치 관리**: GitHub Flow / Git Flow / Trunk-Based
- **프론트/백엔드 협업**: 프론트 REQ 는 인터랙션을 기술하고 `dev` 단계에서 백엔드 API 와 자동 매칭
- **PR 리뷰 & 머지**: AI 코드 리뷰, 자동 코멘트 제출, 원클릭 머지
- **Git 이슈 통합**: `--from-issue=#N` 로 Gitea/GitHub 이슈에서 요구사항 생성, 브랜치/커밋/done 전체에서 자동 연동 및 자동 종료
- **크로스 레포 공유**: 프론트/백엔드 다중 레포가 동일한 요구사항을 공유 (메인 레포가 유일한 저장소, 읽기 전용 레포는 직접 읽기, 캐시와 동기화 없음)
- **규범 커밋**: 요구사항 번호가 자동 연결된 Conventional Commits
- **변경 이력**: Git 기록으로부터 자동 생성

### 빠른 시작

**새 프로젝트는 두 단계만으로 시작 가능** (플러그인이 세션 시작 시 안내하며 둘 다 필수):

```bash
# 1. 프로젝트 초기화 (docs/requirements/ 생성, PRD 생성, 레포 바인딩)
/rd:init my-project

# 2. 브랜치 전략 설정 (GitHub Flow / Git Flow / Trunk-Based + 호스팅 종류)
/rd:branch init
```

이후 일상 워크플로우:

```bash
# 3. 요구사항 생성 (AI 문답 → 한 번에 문서 생성)
/rd:new 사용자 포인트 시스템

# 4. 리뷰
/rd:review pass

# 5. 개발 (AI 가 구현 플랜을 생성하고 계층별로 안내)
/rd:dev

# 6. 테스트
/rd:test

# 7. 완료 및 아카이브
/rd:done
```

### 커맨드 레퍼런스

#### 요구사항

| 커맨드 | 설명 |
|--------|------|
| `/rd:req` | 모든 요구사항 리스트 (`--type`, `--module` 필터 지원) |
| `/rd:new [제목]` | 정식 요구사항 생성 (AI Q&A → 문서 생성) |
| `/rd:new-quick [제목]` | 빠른 수정 생성 (작은 버그 / 작은 기능) |
| `/rd:do <설명>` | 스마트 개발 (최적화/리팩토링/업그레이드/소폭 변경, 문서 없음) |
| `/rd:fix <설명>` | 라이트 수정 (버그 수정, 문서 없음) |
| `/rd:edit [REQ-XXX]` | 요구사항 편집 |
| `/rd:show [REQ-XXX]` | 요구사항 상세 보기 (읽기 전용) |
| `/rd:status [REQ-XXX]` | 요구사항 상태 조회 |
| `/rd:review [pass\|reject]` | 리뷰 제출 / 승인 / 반려 |
| `/rd:dev [REQ-XXX]` | 개발 시작 또는 계속 |
| `/rd:test [REQ-XXX]` | 종합 테스트 |
| `/rd:test_regression` | 기존 자동화 테스트 실행 |
| `/rd:test_new` | 새 기능용 테스트 케이스 작성 |
| `/rd:done [REQ-XXX]` | 완료 및 아카이브 |
| `/rd:upgrade <QUICK-XXX>` | 빠른 수정을 정식 요구사항으로 승격 |
| `/rd:split [설명]` | 요구사항 단위 분석 및 분할 제안 |

#### PR 리뷰 & 머지

| 커맨드 | 설명 |
|--------|------|
| `/rd:pr [REQ-XXX]` | PR 생성 (GitHub / Gitea 자동 감지) |
| `/rd:pr status` | PR 상태 조회 |
| `/rd:pr review` | AI 코드 리뷰, 코멘트 제출 |
| `/rd:pr comments` | PR 코멘트를 가져와 수정 목록 생성 후 적용 |
| `/rd:pr merge` | PR 머지 (merge/squash/rebase 지원) |

#### 문서 관리

| 커맨드 | 설명 |
|--------|------|
| `/rd:prd` | PRD 상태 개요 |
| `/rd:prd-edit [섹션]` | PRD 편집 |
| `/rd:modules` | 모든 모듈 리스트 |
| `/rd:specs` | 스펙 문서 (데이터 타입, API 계약 등) |

#### 버전 & 브랜치

| 커맨드 | 설명 |
|--------|------|
| `/rd:commit [메시지]` | 요구사항 번호가 자동 연결된 규범 커밋 |
| `/rd:changelog <version>` | 릴리즈 노트 생성 |
| `/rd:branch init` | 브랜치 전략 설정 |
| `/rd:branch hotfix [설명]` | 핫픽스 브랜치 생성 |

#### 프로젝트 설정

| 커맨드 | 설명 |
|--------|------|
| `/rd:init <project-name>` | 프로젝트 초기화 |
| `/rd:use <메인 레포 경로>` | 메인 레포를 바인딩, 현재 레포는 읽기 전용으로 설정 |
| `/rd:projects` | 현재 요구사항 프로젝트 조회 |
| `/rd:migrate` | v2 레이아웃에서 `.devflow/` 로 마이그레이션 |
| `/rd:update-template` | 플러그인 최신 템플릿 동기화 |

### 요구사항 생명 주기

```
정식 (REQ):      초안 → 리뷰 대기 → 리뷰 통과 → 개발 중 → 테스트 중 → 완료
빠른 수정 (QUICK): 초안 → 개발 중 → 테스트 중 → 완료 (리뷰만 생략)
```

### 문서 구조

| 영역 | 섹션 | 작성 방식 |
|------|------|-----------|
| 요구사항 정의 | I–VI (설명, 기능 리스트, 규칙, 시나리오, 데이터 & UX, 테스트 포인트) | AI Q&A → 한 번에 생성 |
| 프로세스 로그 | VII–IX (리뷰, 변경 이력, 연결 정보) | 커맨드가 자동 작성 |
| 구현 플랜 | X (데이터 모델, API 설계, 파일 변경, 구현 단계) | `/rd:dev` 단계에서 생성 |

### 크로스 레포 공유

```
~/backend/   (primary)  → docs/requirements/  유일한 저장소, git 관리, 쓰는 즉시 반영
~/frontend/  (readonly) → /rd:use ~/backend 바인딩 후 메인 레포 요구사항을 직접 읽음, dev 단계에서 백엔드 API 자동 매칭
```

설정은 `.devflow/settings.json`(팀 공유, git 포함)과 `.devflow/settings.local.json`(시크릿 및 로컬 경로, git 미포함)에 있습니다. v2 에서 업그레이드했거나 이름이 변경된 req 에서 rd 로 옮긴 프로젝트는 `/rd:migrate` 를 실행하세요.

### AI 스킬 (자동 트리거)

| 스킬 | 트리거 |
|------|--------|
| `requirement-analyzer` | 요구사항 생성/편집 시 — AI Q&A → 문서 생성 |
| `dev-guide` | 개발 중 — 계층별 가이드 + 실시간 문서 유지보수 |
| `quick-fix-guide` | 빠른 수정 — 신속한 분석 및 플랜 |
| `test-guide` | 테스트 단계 — 회귀 및 신규 테스트 작성 |
| `prd-analyzer` | PRD 편집 시 — 각 섹션 작성 지원 |
| `code-impact-analyzer` | 요구사항 변경 시 — 코드 영향 분석 |
| `changelog-generator` | 릴리즈 노트 생성 |

---

## pm 플러그인 — 프로젝트 관리 도우미

PRD, 요구사항 문서, Git 기록에서 프로젝트 데이터를 추출하여 다양한 대상자에 맞춘 리포트, 통계, 기획안을 생성합니다.

- **읽기 전용**: rd 가 생성한 데이터를 소비하며 요구사항 문서는 수정하지 않음
- **rd 없이도 동작**: 요구사항 데이터가 없어도 Git 통계와 자유 질의응답은 사용 가능
- **선택적 저장**: 모든 출력은 `docs/reports/` 에 저장 가능

| 커맨드 | 설명 |
|--------|------|
| `/pm` | 프로젝트 대시보드 |
| `/pm:weekly` | 주간 리포트 |
| `/pm:monthly` | 월간 리포트 |
| `/pm:milestone <버전>` | 마일스톤/릴리즈 요약 |
| `/pm:stats` | 다차원 통계 |
| `/pm:progress` | 프로젝트 진척도 (간트 뷰) |
| `/pm:plan <주제>` | 기획안 문서 (일정/기술/리소스) |
| `/pm:risk` | 리스크 스캔 |
| `/pm:standup` | 스탠드업 요약 |
| `/pm:ask <질문>` | 프로젝트 데이터 기반 자유 질의응답 |

---

## api 플러그인 — API 연동

프론트엔드 API 연동 툴킷으로 Swagger/OpenAPI 파싱, 필드 매핑, 코드 생성을 지원합니다.

| 커맨드 | 설명 |
|--------|------|
| `/api:import` | Swagger 문서 임포트 |
| `/api:search <키워드>` | 엔드포인트 검색 |
| `/api:gen` | TypeScript 타입 및 요청 함수 생성 |
| `/api:map` | 필드 매핑 분석 |

---

## diag 플러그인 — 프로덕션 진단

운영 환경 에러를 자연어로 설명하면, 플러그인이 SSH 로 로그를 읽기 전용으로 가져와 스택을 분석하고 로컬 코드와 연결해 수정 제안을 제공합니다. **전 과정 읽기 전용**: SSH 호스트 화이트리스트, 커맨드 동사 화이트리스트, 쓰기 작업 차단, 민감 입력 차단 등 리스크 관리 Hook 이 모두 강제 적용되며, 모든 SSH 커맨드는 감사 로그로 기록됩니다.

| 커맨드 | 설명 |
|------|------|
| `/diag:init` | 서비스 목록 설정 (호스트, 로그 경로) |
| `/diag:diagnose <에러 설명>` | 로그 수집 → 스택 분석 → 코드 연결 → 수정 제안 |
| `/diag:audit` | 감사 기록 조회 |

자세한 내용은 [plugins/diag/README.md](plugins/diag/README.md) 참고.

---

## 튜토리얼

전체 단계별 튜토리얼: [docs/tutorial.ko.md](docs/tutorial.ko.md).

## 라이선스

[Apache License 2.0](LICENSE)
