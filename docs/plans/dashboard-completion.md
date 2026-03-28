# Plan: Dashboard 미완성 요소 4종 수정

## 상태: ✅ 완료 (2026-03-16)

## Context

`ytai.hakhamsolution.co.kr` 대시보드에 4가지 미완성 요소가 발견됨:
1. `/pipelines` 라우트 404 (목록 페이지 없음)
2. Channels 페이지 전체가 하드코딩 Mock 데이터 (API 미연결)
3. Onboarding Step 2 채널 생성 버튼이 API 호출 없이 `goNext()`만 실행
4. Dashboard API 실패 시 일반 에러 메시지 (API 키 미설정 케이스 미구분)

모두 프론트엔드 전용 수정. 백엔드 변경 없음.

---

## 수정 대상 파일

| Fix | 액션 | 파일 경로 | 상태 |
|-----|------|-----------|------|
| Fix 4 | 수정 | `packages/frontend/src/app/(app)/page.tsx` | ✅ 완료 |
| Fix 3 | 수정 | `packages/frontend/src/app/(app)/onboarding/page.tsx` | ✅ 완료 |
| Fix 2 | 전체 교체 | `packages/frontend/src/app/(app)/channels/page.tsx` | ✅ 완료 |
| Fix 1 | 신규 생성 | `packages/frontend/src/app/(app)/pipelines/page.tsx` | ✅ 완료 |

---

## 재사용할 기존 훅/유틸

- `usePipelineRuns(params?)` — `packages/frontend/src/hooks/use-pipeline.ts`
  - params: `{ channel_id?, status?, limit?, offset? }`
  - 반환: `PipelineRunsResponse { runs, total, limit, offset }`
- `useChannels()` / `useCreateChannel()` — `packages/frontend/src/hooks/use-channels.ts`
  - `Channel` 타입: `{ channel_id, name, category, has_brand_guide }`
  - `CreateChannelRequest`: `{ channel_id, name, category? }` ← `description` 필드 없음
- `ApiError` — `packages/frontend/src/lib/api.ts` (status 코드 포함)

---

## Fix 4: Dashboard 에러 상태 개선

**파일:** `packages/frontend/src/app/(app)/page.tsx`

1. `import { ApiError } from '@/lib/api'` 추가
2. lucide-react에 `Settings` 아이콘 추가
3. `error` 블록에서 `ApiError` 401/403 여부 분기:
   - 인증 에러: "API 키가 설정되지 않았습니다" + `/settings` 링크 버튼 (auth가 기본 탭)
   - 그 외: 기존 메시지 유지

---

## Fix 3: Onboarding Step 2 API 연결

**파일:** `packages/frontend/src/app/(app)/onboarding/page.tsx`

1. `import { useCreateChannel } from '@/hooks/use-channels'` 추가
2. lucide-react에 `Loader2`, `AlertCircle` 추가
3. `slugify` 헬퍼 함수 추가 (파일 상단):
   ```ts
   function slugify(text: string): string {
     return text.toLowerCase().trim()
       .replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '').replace(/-+/g, '-');
   }
   ```
4. `CreateChannelStep` 내부 수정:
   - `useCreateChannel()` 훅 추가
   - `apiError` state 추가
   - 버튼 `onClick` → `handleCreate` 비동기 함수:
     - `slugify(channelName)`로 `channel_id` 생성 (빈 값 가드)
     - `createChannel.mutateAsync({ channel_id, name, category: 'general' })` 호출
       - description/targetAudience는 API 미지원 → UI에만 유지, 전송 안 함
     - 성공 시 `onNext()`, 실패 시 `apiError` 표시 (409 → 중복 안내)
   - 버튼: `isPending` 중 Loader2 아이콘 + 비활성화
   - `CardContent` 하단에 에러 표시 div 추가

---

## Fix 2: Channels 페이지 실제 API 연결

**파일:** `packages/frontend/src/app/(app)/channels/page.tsx` (전체 교체)

**제거:** 하드코딩 mock 데이터, Progress/quota bar, 구독자 수, YouTube 인증 상태, `href="#"` 링크

**추가:**
1. `useChannels()` 훅으로 실제 채널 목록 로드
2. `useCreateChannel()` + Dialog로 인라인 채널 생성 (Settings 패턴 동일)
3. `slugify` 헬퍼 — name → channel_id 자동 생성 (읽기전용으로 표시)
4. `getAvatarBg(category)` 헬퍼 — 카테고리별 색상 반환:
   ```ts
   { technology: 'bg-blue-500/20 text-blue-400', education: 'bg-green-500/20 ...',
     entertainment: 'bg-purple-500/20 ...', business: 'bg-orange-500/20 ...',
     general: 'bg-primary/20 text-primary' }
   ```
5. 카드 구조:
   - CardHeader: 아바타(첫 글자) + name + category
   - CardContent: `has_brand_guide` 배지 (`BookOpen` 아이콘)
   - "Manage on Studio" 링크 완전 제거 (YouTube ID 데이터 없음)
6. 상태별 렌더링:
   - 로딩: 3개 Skeleton 카드
   - 에러: AlertCircle + 에러 메시지
   - 빈 목록: Inbox 아이콘 + "채널이 없습니다" (col-span-full)
   - 데이터: 실제 채널 카드 grid (md:2, lg:3)

---

## Fix 1: Pipelines 목록 페이지 신규 생성

**파일:** `packages/frontend/src/app/(app)/pipelines/page.tsx` (신규)

1. `usePipelineRuns({ status: filter || undefined })` 훅 사용
2. 상태 필터 버튼: All / Pending / Running / Completed / Failed
   - `variant="secondary"` = 활성, `variant="ghost"` = 비활성
3. 헬퍼 함수:
   - `getStatusBadge(status)` — 기존 dashboard/[id] 패턴과 동일
   - `formatDuration(createdAt, completedAt)` — ms 계산 후 `"Xm Ys"` 형식
4. 테이블 컬럼: Topic | Channel | Status | Created | Duration
   - 행 클릭 → `useRouter().push('/pipelines/${run_id}')` (cursor-pointer + hover:bg-muted/50)
5. 상태별 렌더링:
   - 로딩: 5행 Skeleton Table
   - 에러: XCircle + 메시지
   - 빈 목록: Inbox 아이콘 + "파이프라인 없음" + "New Pipeline" 버튼
   - 데이터: Table (TableHeader + TableBody)
6. 페이지 헤더: "Pipelines" 제목 + "New Pipeline" 버튼 (`/pipelines/new`)

---

## 구현 순서

Fix 4 → Fix 3 → Fix 2 → Fix 1 (영향 범위 작은 것부터)

---

## 검증 방법

1. `make server` 실행 후 `http://localhost:3000` 접속
2. API 키 미설정 상태에서 Dashboard → "API 키 설정" 버튼 표시 확인
3. `/onboarding` 접속 → Step 2에서 채널 생성 → API 실제 호출 확인
4. `/channels` 접속 → 실제 채널 목록 표시, "Connect Channel" 다이얼로그 동작 확인
5. `/pipelines` 접속 → 목록 페이지 404 해소, 필터/클릭 동작 확인
