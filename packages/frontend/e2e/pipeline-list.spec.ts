import { test, expect } from '@playwright/test';

const MOCK_RUNS = [
    {
        run_id: 'run-001',
        channel_id: 'channel-a',
        topic: 'Topic A',
        status: 'completed',
        dry_run: false,
        created_at: new Date(Date.now() - 3600000).toISOString(),
        completed_at: new Date().toISOString(),
    },
    {
        run_id: 'run-002',
        channel_id: 'channel-b',
        topic: 'Topic B',
        status: 'failed',
        dry_run: false,
        created_at: new Date(Date.now() - 7200000).toISOString(),
        completed_at: null,
    },
    {
        run_id: 'run-003',
        channel_id: 'channel-a',
        topic: 'Topic C',
        status: 'running',
        dry_run: false,
        created_at: new Date().toISOString(),
        completed_at: null,
    },
];

test.describe('Pipeline List', () => {
    test.beforeEach(async ({ page }) => {
        await page.route('**/api/v1/pipeline/runs**', (route) => {
            const url = new URL(route.request().url());
            const statusFilter = url.searchParams.get('status');
            const runs = statusFilter
                ? MOCK_RUNS.filter((r) => r.status === statusFilter)
                : MOCK_RUNS;

            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ runs, total: runs.length, limit: 20, offset: 0 }),
            });
        });
    });

    test('파이프라인 목록이 렌더링된다', async ({ page }) => {
        await page.goto('/pipelines');

        await expect(page.getByText('Topic A')).toBeVisible();
        await expect(page.getByText('Topic B')).toBeVisible();
        await expect(page.getByText('Topic C')).toBeVisible();
    });

    test('행 클릭 시 상세 페이지로 이동한다', async ({ page }) => {
        // Mock detail page
        await page.route('**/api/v1/pipeline/runs/run-001', (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    ...MOCK_RUNS[0],
                    brand_name: '',
                    current_agent: null,
                    result: null,
                    errors: [],
                    updated_at: MOCK_RUNS[0].created_at,
                }),
            })
        );

        await page.goto('/pipelines');
        await page.getByText('Topic A').click();
        await page.waitForURL('**/pipelines/run-001');
    });
});
