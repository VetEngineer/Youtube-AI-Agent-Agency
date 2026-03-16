import { test, expect } from '@playwright/test';

const RUN_ID = 'run-active-001';

test.describe('Pipeline Cancel', () => {
    test.beforeEach(async ({ page }) => {
        await page.route(`**/api/v1/pipeline/runs/${RUN_ID}`, (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    run_id: RUN_ID,
                    channel_id: 'test-channel',
                    topic: 'Active Topic',
                    status: 'running',
                    current_agent: 'script_writer',
                    dry_run: false,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    completed_at: null,
                    errors: [],
                }),
            })
        );

        await page.route(`**/api/v1/pipeline/runs/${RUN_ID}/cancel`, (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ run_id: RUN_ID, status: 'cancelled' }),
            })
        );

        // SSE stream mock (returns immediately)
        await page.route(`**/api/v1/pipeline/runs/${RUN_ID}/stream`, (route) =>
            route.fulfill({
                status: 200,
                contentType: 'text/event-stream',
                body: `data: {"run_id":"${RUN_ID}","status":"running","current_agent":"script_writer","errors":[]}\n\n`,
            })
        );
    });

    test('활성 파이프라인에 Cancel 버튼이 표시된다', async ({ page }) => {
        await page.goto(`/pipelines/${RUN_ID}`);
        await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
    });

    test('Cancel 버튼 클릭 시 취소 API가 호출된다', async ({ page }) => {
        let cancelCalled = false;
        await page.route(`**/api/v1/pipeline/runs/${RUN_ID}/cancel`, (route) => {
            cancelCalled = true;
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ run_id: RUN_ID, status: 'cancelled' }),
            });
        });

        await page.goto(`/pipelines/${RUN_ID}`);
        await page.getByRole('button', { name: /cancel/i }).click();

        await expect(async () => {
            expect(cancelCalled).toBe(true);
        }).toPass({ timeout: 3000 });
    });
});
