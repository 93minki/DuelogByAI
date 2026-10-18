# 듀얼로그(Duelog) 설계 문서 v1

> 사회자·찬성·반대 3개의 AI가 웹 검색 근거로 토론하고, 사용자는 그 과정을 실시간으로 지켜본 뒤 요약을 받는 서비스.

---

## 1. 확정된 요구사항

| 영역 | 결정 |
|---|---|
| LLM | OpenAI 고정. 역할별 모델은 `.env`에서 변경 |
| 웹 검색 | Exa. 발언당 검색 횟수 제한 없음. 단, 무한 루프 방지용 안전 상한 20회 |
| 출처 제외 | 블로그·커뮤니티 도메인 제외. 나무위키는 허용 |
| 주제 판정 | TypeSafe JEV(`jev-latest`)를 공식 API로 직접 호출. LLM 호출 전 가드레일 |
| 토론 불가 기준 | 정답이 하나인 사실 질문 / 의미 없는 입력·단순 인사 / 개인 고민 상담 / 유해 주제(혐오·범죄 방법·특정 개인 비방). 정치·종교·젠더 등 민감 주제는 허용 |
| 거부 사유 | 사유 유형별 고정 문구로 안내 |
| 명사형 주제 | 통과시키고, 사회자가 "~해야 한다" 형태의 논제로 정리하고 찬반 입장을 정의 |
| 라운드 | 1R 입론 → 2~3R 반박과 새 근거 → 3R 이후 사회자가 4·5R 연장 여부 결정 → 최종 발언(새 근거 없음, 횟수에 미포함) |
| 순서 | 라운드마다 사회자 안내 → 찬성 → 반대 |
| 사회자 | 철저한 중립. 쟁점 정리와 다음 논점 제시만 하고, 사실 정정은 하지 않음 |
| 발언 길이 | 한글 600~1,000자 |
| 근거 부족 | 검색 근거가 없는 주장은 버리고 다른 주장으로 대체(프롬프트로 강제) |
| 출처 표기 | `[1]`, `[2]`. 번호는 토론 전체에서 공통. 실제 Exa 결과에 없는 번호는 코드에서 제거 |
| 승패 | 없음. 평가하는 표현 금지 |
| 요약 | 찬성 요약 / 반대 요약 / 최종 요약(핵심 쟁점·합의점·대립점·미해결 질문) |
| 실시간 | SSE 토큰 스트리밍과 검색 상태 표시. 사용자는 끼어들 수 없고 종료만 가능 |
| 중단 | 진행된 발언까지 저장하고 `stopped` 상태로 둠. 요약은 생략 |
| 이탈 | 서버에서 계속 진행. 재접속하면 이어 보기. 사용자당 동시 진행 1개 |
| 언어 | 한국어만 |
| 인증 | 이메일과 비밀번호(최소 8자). JWT를 httpOnly 쿠키로 저장, 7일 유지. 이메일 인증·비밀번호 재설정 없음 |
| 사용량 제한 | 사용자당 하루 10회(`.env`로 조정) |
| 주제 길이 | 2~200자 (명사형 주제 허용을 위해 5자에서 변경) |
| 대시보드 | 목록, 상세, 삭제(hard delete) |
| 랜딩 | 서비스 소개와 하드코딩된 샘플 토론 1개 |
| UI | Tailwind, shadcn/ui. 다크모드 지원 |
| 실행 | 로컬 실행과 Docker Compose |

---

## 2. 아키텍처

```
[Next.js :3000] ──(rewrites /api/*)──▶ [FastAPI :8000] ──▶ PostgreSQL :5432
     │  SSE 수신                            │
     │                                      ├─ JEV  (api.typesafe.ai/v1/systemone)
     │                                      ├─ OpenAI (langchain-openai)
     │                                      └─ Exa  (exa-py)
     │
     └─ 쿠키(JWT)는 같은 출처(:3000)로 전송되고, Next가 백엔드로 프록시
```

- **토론 실행**: FastAPI 프로세스 안의 asyncio 백그라운드 태스크에서 LangGraph 그래프를 실행합니다.
- **실시간 전달**: 토론마다 인메모리 브로드캐스터(asyncio.Queue 구독자 목록)를 두고 SSE로 내보냅니다.
- **재시작 복구**: LangGraph `AsyncPostgresSaver` 체크포인터가 노드(발언) 하나가 끝날 때마다 상태를 Postgres에 저장합니다. 서버가 시작될 때 `running` 상태인 토론을 찾아 **마지막으로 완료된 발언 다음부터 이어서 실행**합니다. 작성 도중이던 발언 하나만 다시 생성됩니다.
- **Redis/Celery**: 1차 버전에서는 사용하지 않습니다. 서버를 여러 대로 확장하는 시점에 작업 큐로 분리합니다.

---

## 3. 디렉터리 구조

```
DuelogByAI/
├─ docker-compose.yml
├─ .env.example
├─ docs/DESIGN.md
├─ backend/
│  ├─ pyproject.toml          # uv, Python 3.12
│  ├─ alembic/  alembic.ini
│  ├─ Dockerfile
│  ├─ app/
│  │  ├─ main.py              # FastAPI 앱, lifespan(체크포인터 준비, 복구)
│  │  ├─ config.py            # pydantic-settings
│  │  ├─ db.py                # async SQLAlchemy 엔진/세션
│  │  ├─ models.py            # ORM 모델
│  │  ├─ schemas.py           # API 요청/응답 스키마
│  │  ├─ auth/                # 해싱, JWT, 의존성, 라우터
│  │  ├─ debates/             # 라우터, 서비스, 러너(백그라운드), 브로드캐스터
│  │  ├─ guard/jev.py         # JEV 클라이언트와 판정 로직
│  │  ├─ search/exa.py        # Exa 검색, 도메인 제외, 출처 레지스트리
│  │  └─ graph/
│  │     ├─ state.py          # DebateState
│  │     ├─ prompts.py        # 역할별 시스템 프롬프트
│  │     ├─ nodes.py          # 사회자/토론자/요약 노드
│  │     ├─ speaker.py        # 검색 도구 루프와 토큰 스트리밍
│  │     ├─ citations.py      # [n] 검증과 정리
│  │     └─ builder.py        # 그래프 구성
│  └─ tests/
└─ frontend/
   ├─ package.json            # pnpm, Next.js(App Router), TS
   ├─ Dockerfile
   ├─ middleware.ts           # 비로그인 사용자를 /login으로 보냄
   └─ src/
      ├─ app/  (page.tsx 랜딩, login, signup, dashboard, debates/[id])
      ├─ components/ (ui/ shadcn, debate/, landing/)
      └─ lib/ (api.ts, sse.ts, sample-debate.ts)
```

---

## 4. 데이터베이스 스키마

```
users
  id uuid PK, email citext UNIQUE, password_hash text, created_at timestamptz

debates
  id uuid PK, user_id uuid FK→users ON DELETE CASCADE
  topic_raw text                -- 사용자 입력
  proposition text NULL         -- 사회자가 정리한 논제
  pro_stance text NULL, con_stance text NULL
  status enum(running, completed, stopped, failed)
  current_round int, total_rounds int NULL
  jev_result jsonb              -- 판정 원본(감사용)
  error text NULL
  created_at, completed_at NULL

turns                           -- 발언 하나 = 한 행
  id uuid PK, debate_id FK CASCADE, seq int  (debate_id, seq) UNIQUE
  round int                     -- 0 = 개회, 1..5, 99 = 최종 발언
  phase enum(opening_remarks, moderation, opening, rebuttal, closing)
  speaker enum(moderator, pro, con)
  content text                  -- [n] 정리가 끝난 최종 본문
  search_queries jsonb          -- 이 발언 중 실행한 검색어 목록
  created_at

sources                         -- 토론 전체에서 공통 번호
  id uuid PK, debate_id FK CASCADE, number int  (debate_id, number) UNIQUE
  url text (debate_id, url) UNIQUE, title text, published_date text NULL
  author text NULL, excerpt text

summaries
  debate_id uuid PK FK CASCADE
  pro_summary text, con_summary text
  final_summary jsonb           -- {overview, key_issues[], agreements[], disagreements[], open_questions[]}
  created_at
```

LangGraph 체크포인트 테이블은 `AsyncPostgresSaver.setup()`이 별도로 만듭니다. 토론을 삭제할 때는 해당 thread의 체크포인트도 함께 지웁니다.

---

## 5. 주제 판정 (JEV)

`POST /api/debates` 안에서 토론을 만들기 전에 실행합니다. 요청 형식은 다음과 같습니다.

```json
{
  "model": "jev-latest",
  "state": { "topic": "<사용자 입력>" },
  "questions": {
    "verdict": {
      "type": "choice",
      "instructions": "`topic`이 찬성과 반대 양측이 근거를 들어 논쟁할 수 있는 토론 주제인지 판단하라. ...(경계 사례 명시)",
      "criteria": {
        "debatable": "합리적인 사람들 사이에서 찬반이 실제로 갈리는 정책·가치·사회 쟁점. 정치·종교·젠더 등 민감 주제와 명사만 있는 주제(예: 사형제도)도 포함",
        "not_debatable": "정답이 하나인 사실 질문, 의미 없는 입력이나 인사, 개인 고민 상담, 혐오·범죄 방법·특정 개인 비방 등 유해한 주제",
        "ambiguous": "무엇을 두고 찬반을 나눌지 알 수 없을 만큼 모호하거나 범위가 지나치게 넓음"
      }
    },
    "reason": {
      "type": "choice",
      "instructions": "`topic`이 토론 주제로 부적합하다면 가장 가까운 이유를 고르라",
      "criteria": { "factual": "...", "meaningless": "...", "personal": "...", "harmful": "...", "none": "부적합하지 않음" }
    }
  }
}
```

판정 규칙(기준값은 `.env`로 조정):

1. `verdict = debatable`이고 confidence ≥ `JEV_MIN_CONFIDENCE`(기본 0.6)이면 **통과**
2. `verdict = not_debatable`이고 confidence ≥ 기준값이면 **거부**. `reason`에 맞는 고정 문구를 표시
3. 그 밖의 경우(`ambiguous`이거나 confidence가 낮음)는 **애매** → "조금 더 구체적으로 작성해 주세요"

JEV가 첫 번째 선택지를 고르는 경향이 있어, 실제 키로 테스트할 때 선택지 순서를 바꿔 결과가 같은지 확인합니다. 응답은 400·422로 돌려주며 `{status: "rejected"|"ambiguous", reason, message}` 형태입니다.

---

## 6. LangGraph 흐름

```
START
 → frame_topic        사회자: 논제 정리, 찬반 입장 정의, 개회 발언 (구조화 출력과 스트리밍)
 → moderator_round    사회자: 라운드 안내 (2R부터는 직전 쟁점 정리와 다음 논점 제시)
 → pro_speech         찬성: 검색 루프 → 발언
 → con_speech         반대: 검색 루프 → 발언
 → round_check        round < 3 → moderator_round
                      3 ≤ round < 5 → 사회자가 연장 판단(구조화 출력: continue, reason)
                      그 외 → closing_intro
 → closing_intro      사회자: 최종 발언 안내
 → pro_closing → con_closing   (검색 없음, 기존 출처 번호만 인용 가능)
 → summarize          구조화 출력: pro_summary, con_summary, final_summary
 → END
```

**발언자 루프** (`speaker.py`):
- OpenAI 모델에 `web_search(query)` 도구를 연결하고 tool-call 루프를 돕니다. 루프는 최대 20회입니다.
- 검색 결과는 출처 레지스트리에 등록되어 전체 공통 번호 `[n]`을 받습니다. 모델에는 `[n] 제목 / 날짜 / 발췌` 형태로 전달합니다.
- 최종 답변 토큰은 SSE `token` 이벤트로 스트리밍합니다.

**출처 검증** (`citations.py`):
- 본문의 `[n]` 중 레지스트리에 없는 번호는 제거합니다.
- 유효한 출처가 하나도 없는 발언(최종 발언 제외)은 "근거 부족"으로 보고 한 번 다시 생성합니다.

**프롬프트 원칙**:
- 토론자: 학습된 지식으로 주장 금지. 모든 사실 주장에 `[n]` 필수. 근거를 찾지 못한 주장은 버리고 다른 주장으로 대체. 2R부터는 상대 직전 발언의 근거를 구체적으로 반박하고 새 근거 추가. 600~1,000자.
- 사회자: 어느 쪽에도 유리한 표현 금지. 평가·판정·사실 정정 금지. 쟁점 정리와 질문만.
- 요약: 각 측 주장을 그대로 압축. "더 설득력 있는", "우세한" 같은 평가 어휘 금지.

---

## 7. API

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/auth/signup` | `{email, password}` → 가입 후 쿠키 설정 |
| POST | `/api/auth/login` | 쿠키 설정 |
| POST | `/api/auth/logout` | 쿠키 삭제 |
| GET | `/api/auth/me` | 현재 사용자 |
| GET | `/api/debates` | 내 토론 목록(최신순) |
| POST | `/api/debates` | `{topic}` → JEV 판정, 통과하면 생성하고 실행 시작. 일일 한도·동시 진행 검사 |
| GET | `/api/debates/{id}` | 상세: 토론, 완료된 발언, 출처, 요약 |
| GET | `/api/debates/{id}/stream` | SSE 실시간 이벤트 |
| POST | `/api/debates/{id}/stop` | 중단 |
| DELETE | `/api/debates/{id}` | 삭제(진행 중이면 먼저 중단) |

**SSE 이벤트**: `framed`(논제·입장), `turn_start`(turn_id, speaker, round, phase), `search`(query), `token`(delta), `turn_end`(정리된 본문, 새 출처), `round_decision`(continue, reason), `summary`, `status`(completed·stopped·failed).

**재접속**: 먼저 `GET /{id}`로 완료된 발언을 그리고, 이어서 `/stream`에 연결합니다. 연결 시 서버는 작성 중인 발언의 현재까지 내용을 먼저 보낸 뒤 실시간 토큰을 이어서 보냅니다.

---

## 8. 화면

- **`/` 랜딩**: 히어로(서비스 소개와 시작 버튼), 작동 방식 3단계, 하드코딩 샘플 토론 미리보기(요약 포함), 특징(웹 근거·출처·중립)
- **`/signup`, `/login`**: 이메일·비밀번호 폼
- **`/dashboard`**: 상단에 새 주제 입력(판정 결과를 폼 아래에 안내), 아래에 이전 토론 카드 목록(상태 배지, 날짜, 삭제)
- **`/debates/[id]`**:
  - 상단에 논제와 찬반 입장 고정, 진행 중이면 "토론 종료" 버튼
  - 본문은 라운드별로 구분한 발언 카드. 사회자는 가운데 중립색, 찬성은 왼쪽 파랑, 반대는 오른쪽 주황
  - 검색 중일 때 "🔍 '…' 검색 중" 표시
  - `[n]`에 마우스를 올리면 출처 툴팁, 클릭하면 출처 목록으로 이동
  - 끝에 요약 카드 3개와 전체 출처 목록
- 다크모드는 `next-themes`, 헤더에 토글

---

## 9. 환경 변수 (`.env.example`)

```
DATABASE_URL=postgresql+asyncpg://duelog:duelog@localhost:5432/duelog
JWT_SECRET=change-me
JWT_EXPIRE_DAYS=7
OPENAI_API_KEY=
OPENAI_MODEL_MODERATOR=gpt-5-mini
OPENAI_MODEL_DEBATER=gpt-5
OPENAI_MODEL_SUMMARY=gpt-5-mini
EXA_API_KEY=
EXA_NUM_RESULTS=5
TYPESAFE_API_KEY=
JEV_MODEL=jev-latest
JEV_MIN_CONFIDENCE=0.6
DAILY_DEBATE_LIMIT=10
MAX_SEARCH_CALLS_PER_TURN=20
BACKEND_URL=http://localhost:8000   # Next rewrites 대상
```

Exa 제외 도메인은 코드 상수로 둡니다. 블로그: blog.naver.com, tistory.com, brunch.co.kr, velog.io, medium.com 등. 커뮤니티: dcinside.com, fmkorea.com, theqoo.net, ruliweb.com, clien.net, ppomppu.co.kr, instiz.net, pann.nate.com, reddit.com, quora.com 등.

---

## 10. 테스트

- pytest와 pytest-asyncio를 사용하고, 외부 API(OpenAI·Exa·JEV)는 모두 모킹합니다.
- 대상: JEV 판정 규칙, 출처 레지스트리와 `[n]` 검증, 그래프 라운드 분기(3R 종료·연장·최대 5R), 인증, 토론 API 권한(남의 토론 접근 차단), 일일 한도.
- 프론트엔드: 1차에서는 `pnpm build`와 타입 체크만 확인합니다.

---

## 11. 구현 순서

1. 저장소 초기화(git), docker-compose, 백엔드 골격, DB 모델, Alembic
2. 인증 API와 테스트
3. JEV 가드, Exa 검색, 출처 레지스트리와 테스트
4. LangGraph 그래프, 러너, 브로드캐스터, SSE, 복구와 테스트
5. 프론트엔드: 레이아웃, 다크모드, 인증 페이지, 미들웨어
6. 대시보드, 토론 실시간 화면, 요약
7. 랜딩과 샘플 토론
8. Docker Compose 전체 기동 확인과 README
