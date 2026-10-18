# 듀얼로그 (Duelog)

사회자·찬성·반대 3개의 AI가 웹 검색 근거와 출처를 들어 토론하는 서비스입니다. 설계는 [docs/DESIGN.md](docs/DESIGN.md)를 참고하세요.

- **Frontend**: Next.js 16 (App Router), Tailwind CSS 4, shadcn/ui — `frontend/`
- **Backend**: FastAPI, LangGraph, SQLAlchemy(async), Alembic — `backend/`
- **외부 API**: OpenAI(토론), Exa(웹 검색), TypeSafe JEV(주제 판정)
- **DB**: PostgreSQL (서비스 데이터 + LangGraph 체크포인트)

## 1. 환경 변수

```bash
cp .env.example .env
```

`.env`에 `OPENAI_API_KEY`, `EXA_API_KEY`, `TYPESAFE_API_KEY`를 채우고, `JWT_SECRET`을 32자 이상 임의 문자열로 바꿉니다.

## 2. Docker Compose로 한 번에 실행

```bash
docker compose up --build
```

- 웹: http://localhost:3000
- API: http://localhost:8000/docs

백엔드 컨테이너가 시작할 때 DB 마이그레이션(`alembic upgrade head`)을 자동 실행합니다.

## 3. 로컬 개발 실행

Postgres만 컨테이너로 띄웁니다.

```bash
docker compose up -d db
```

백엔드 (Python 3.12, [uv](https://docs.astral.sh/uv/)):

```bash
cd backend && uv sync && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --port 8000
```

프론트엔드 (Node 20+, pnpm은 `corepack enable`로 활성화):

```bash
cd frontend && pnpm install && pnpm dev
```

프론트엔드는 `/api/*` 요청을 `BACKEND_URL`(기본 `http://localhost:8000`)로 프록시하므로, 브라우저에서는 http://localhost:3000 만 열면 됩니다.

## 4. 테스트

```bash
cd backend && uv run pytest
```

외부 API(OpenAI, Exa, JEV)는 모두 가짜 객체로 대체해 테스트합니다. 범위: 인증, 토론 API 권한·제한, JEV 판정 규칙, 출처 번호 검증, 그래프 라운드 분기(3라운드·연장·최대 5라운드), 근거 없는 발언 재생성, 서버 재시작 후 체크포인트 복구, 중단.

## 5. 동작 메모

- **주제 판정**: 토론 생성 요청 시 JEV `choice` 질문으로 `debatable / not_debatable / ambiguous`를 판정합니다. 신뢰도가 `JEV_MIN_CONFIDENCE` 미만이면 "애매"로 처리합니다. 통과한 주제만 LLM을 호출합니다.
- **출처 검증**: 토론자가 본문에 쓴 `[n]` 중 실제 Exa 검색 결과에 없는 번호는 제거합니다. 유효한 출처가 하나도 없는 발언은 한 번 다시 생성합니다.
- **재시작 복구**: 발언(노드) 하나가 끝날 때마다 LangGraph 체크포인트가 Postgres에 저장됩니다. 서버가 다시 시작되면 `running` 상태의 토론을 마지막 완료 발언 다음부터 이어서 진행합니다.
- **제외 도메인**: 블로그·커뮤니티 도메인 목록은 `backend/app/search/exa.py`의 `EXCLUDED_DOMAINS`에 있습니다.
