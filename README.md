# CareerTrace AI

경험 기록 → GitHub 근거 연결 → 문항 매칭 → 자기소개서 초안 → 근거 확인을 제공하는 **키 없는 로컬 데모 앱**입니다.

이번 버전은 실제 OpenAI 모델을 호출하지 않습니다. 저장·공개 GitHub 조회는 실제 기능이며, STAR 정리·추천·초안 작성은 화면에 명시된 규칙 기반 데모입니다. API 키를 입력하는 것만으로 실제 AI 기능이 활성화되지는 않습니다.

## 실행

필요 환경: Python 3.12 이상, Node.js 22.12 이상. 설치 단계는 인터넷 연결이 필요합니다.

### 팀원이 가져오기

공개 저장소: [hamsikKKKKK/careertrace-ai](https://github.com/hamsikKKKKK/careertrace-ai)

GitHub에서 `hamsikKKKKK` 계정의 `careertrace-ai` 저장소를 찾거나 다음 명령을 실행하세요.

```powershell
git clone https://github.com/hamsikKKKKK/careertrace-ai.git
cd careertrace-ai
./setup.ps1
./run.ps1
```

GitHub Desktop에서는 `File → Clone repository → URL`에 위 저장소 주소를 붙여 넣어도 됩니다. 단순 내려받기는 저장소의 `Code → Download ZIP`을 사용하세요.

소스만 공유됩니다. API 키, 개인 경험·초안 DB, 설치된 라이브러리, 브라우저 시연용 샘플 DB는 업로드하지 않았습니다. 각 팀원의 컴퓨터에서 처음 실행하면 빈 아카이브로 시작하며, **GitHub 경험 발견 → 가상 샘플로 체험**으로 시연할 수 있습니다.

변경 내용을 받아오려면 로컬 수정 사항을 커밋한 뒤 `git pull --ff-only`를 실행하세요. 직접 푸시하려는 팀원은 저장소 협업자 권한이 필요하며, 읽기·복제에는 권한이 필요하지 않습니다.

### 로컬 실행

PowerShell에서 이 폴더로 이동한 뒤:

```powershell
./setup.ps1
./run.ps1
```

설치와 빌드가 완료된 현재 작업 폴더에서는 `./run.ps1`만 실행하면 됩니다. 브라우저에서 <http://127.0.0.1:8000>을 엽니다. `Ctrl+C`로 서버를 중지합니다. 다른 포트는 `./run.ps1 -Port 8001`.

PowerShell 스크립트 대신 직접 실행할 수도 있습니다:

```powershell
./.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000
```

## 사용 흐름

1. **GitHub 경험 발견**에서 공개 저장소 기본 URL을 입력합니다. 네트워크 없이 체험하려면 **가상 샘플로 체험**을 선택합니다.
2. 후보의 원문·작성자·근거 링크를 확인하고 **본인 활동 확인 · 경험 작성**을 누릅니다.
3. 본인이 실제 수행한 행동과 확인한 결과를 입력하고 확인 체크 후 저장합니다. 샘플에는 별도의 **샘플 STAR 내용 채우기** 버튼이 있습니다.
4. **자기소개서 매칭**에서 기업·직무·문항·글자 수를 입력합니다. 예: `어려운 문제를 해결한 경험을 설명해 주세요.`
5. 관련 경험 중 하나로 초안을 만들고 **근거 보기**를 눌러 자료를 확인합니다.
6. 초안을 편집·저장·복사합니다. 저장된 초안은 **작성한 자기소개서**에서 다시 열 수 있습니다.

경험 직접 입력도 가능합니다. 메모의 `상황:`, `역할:`, `행동:`, `결과:` 라벨을 사용하면 STAR 필드로 분리됩니다. 라벨이 없으면 메모를 상황에 그대로 보존하고 빠진 정보에 대해 최대 2개 질문을 표시합니다.

## 구현 범위와 한계

| 기능 | 현재 동작 |
|---|---|
| 경험 등록·수정·검색·유형 필터 | 실제 API·SQLite 저장 |
| 공개 GitHub | 실제 저장소·커밋·PR·이슈 조회, 작성자·원문 URL 보존 |
| 경험 후보 | 활동 원문을 후보로 표시, 사용자 행동·결과 직접 확인 필요 |
| STAR·역량 추출 | 라벨·키워드 규칙 기반 데모, 자유 텍스트 의미 분석 아님 |
| 문항·경험 추천 | 역량·키워드 일치로 최대 3개, 무관한 경험을 강제로 추천하지 않음 |
| 초안 작성 | 확인한 STAR 문장을 그대로 조합, 새 사건·수치 생성 없음 |
| 글자 수 | Unicode 코드 포인트 기준, 공백·줄바꿈 포함, 앞뒤 공백 제외 |
| 초과 처리 | 생성 시 넘치는 문장 제외, 편집 후 초과 저장 거절 |
| 문장 근거 | 경험의 연결 자료를 참고 링크로 표시, 사실 검증 완료 아님 |
| 초안 편집 | 내용 변경 시 모든 자동 문장 근거 연결 해제, 원본 경험 자료는 열람 가능 |
| 샘플 | 명시적 버튼으로만 생성, 경험·초안에 샘플 표시 유지, 대시보드 실제 기록 수에서 제외 |
| 실제 LLM | 미구현. 후속 작업으로 구조화 출력 검증·OpenAI 어댑터·실제 문항 맞춤 생성 필요 |
| 회의록 파일·OAuth·다중 사용자 | 미구현 |

현재 초안은 기업·직무·문항 정보를 편집 화면에 함께 보여주지만, 문장을 기업별로 재작성하지 않습니다. 키워드 추천 점수는 데모 정렬값이며 AI 확률·역량 점수·채용 적합도가 아닙니다. 결과가 없는 경험에는 `결과: 확인 필요` 안내를 표시합니다.

GitHub 조회 범위는 최근 커밋 최대 20개, PR 10개, 이슈 목록 20개(PR 항목 제외)입니다. 이 중 유형을 번갈아 최대 12개 후보를 표시합니다. 빈 저장소, 잘못된 URL, 비공개·없는 저장소, API 호출 제한, 네트워크 실패를 안내합니다. 이동된 저장소 URL은 새 기본 URL을 입력해야 합니다. 인증 없는 호출은 GitHub의 IP별 제한을 받습니다.

## 환경변수·데이터

`.env.example`을 `.env`로 복사해 선택적으로 설정합니다. 설정 변경 후 서버를 재시작하세요.

- `GITHUB_TOKEN`: 선택. GitHub 요청에만 서버에서 사용하며 브라우저에 전달하지 않습니다. 공개 저장소만 지원합니다.
- `DATABASE_URL`: 선택. 기본 DB는 `backend/data/careertrace.db`. 필요하면 절대경로 SQLite URL을 지정합니다.
- `ANALYSIS_MODE=demo`: 이 버전의 고정 동작을 설명하는 값입니다. 다른 값을 넣어도 실제 AI로 전환되지 않습니다.

입력한 경험과 초안은 해당 SQLite 파일에 저장되어 새로고침·서버 재시작 후에도 유지됩니다. 원문에 개인정보가 있다면 로컬 DB에도 남습니다. 백업은 서버를 종료한 뒤 DB 파일을 복사하세요. 삭제·내보내기 UI는 이번 범위에 포함하지 않았습니다.

로그인이 없는 **본인 컴퓨터의 단일 사용자용** 앱입니다. 실행 스크립트는 `127.0.0.1`에만 바인딩합니다. 인터넷 공개 배포 기능은 포함하지 않습니다.

## 개발

```powershell
# 터미널 1
./.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --app-dir backend --reload --host 127.0.0.1 --port 8000
# 터미널 2
cd frontend
npm run dev
```

Vite 개발 서버는 <http://127.0.0.1:5173>, `/api` 요청은 FastAPI로 프록시합니다. 일반 실행은 FastAPI가 빌드된 프론트엔드를 함께 제공합니다. Windows의 잘못된 `.js` MIME 연결은 서버에서 보정합니다.

## 테스트

```powershell
cd backend
../.venv/Scripts/python.exe -m pytest -q
cd ../frontend
npm run build
```

`backend/tests/test_api.py`는 임시 SQLite를 사용합니다. 저장 지속성, 확인 상태, 샘플 표시, 글자 수, 편집 후 근거 해제, 잘못된 URL, GitHub 오류·작성자 보존을 검사합니다. 테스트 중 GitHub 오류 응답은 HTTP transport에서 모의하며, 데이터 저장·분석 로직은 실제 코드를 실행합니다.

검증 기록: [docs/verification.md](docs/verification.md). API 문서: <http://127.0.0.1:8000/docs>.

## 구조

```text
backend/app/     데이터 모델, 검증, 규칙 엔진, GitHub 조회, API
backend/tests/   API·저장·오류 처리 테스트
frontend/src/   React 화면, API 클라이언트, 반응형 스타일
docs/           구현 계획·검증 기록
setup.ps1       의존성 설치와 프론트엔드 빌드
run.ps1         로컬 서버 실행
```

구현 시 참고: [GitHub 공식 commits REST API](https://docs.github.com/en/rest/commits/commits), [Vite 공식 시작 가이드](https://vite.dev/guide/).
