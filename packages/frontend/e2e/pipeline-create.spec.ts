import { test, expect } from '@playwright/test';

const MOCK_RUN_ID = 'test-run-id-create-001';

test.describe('Pipeline Create', () => {
    test.beforeEach(async ({ page }) => {
        // Mock channels API
        await page.route('**/api/v1/channels', (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    channels: [
                        { channel_id: 'test-channel', name: 'Test Channel', category: 'general', has_brand_guide: false },
                    ],
                    total: 1,
                }),
            })
        );

        // Mock pipeline run creation
        await page.route('**/api/v1/pipeline/run', (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    run_id: MOCK_RUN_ID,
                    status: 'pending',
                    channel_id: 'test-channel',
                    topic: 'Test Topic',
                }),
            })
        );

        // Mock pipeline detail
        await page.route(`**/api/v1/pipeline/runs/${MOCK_RUN_ID}`, (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    run_id: MOCK_RUN_ID,
                    channel_id: 'test-channel',
                    topic: 'Test Topic',
                    status: 'pending',
                    current_agent: null,
                    dry_run: false,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                    completed_at: null,
                    errors: [],
                }),
            })
        );
    });

    test('폼 제출 후 상세 페이지로 이동하고 Pending 배지가 표시된다', async ({ page }) => {
        await page.goto('/pipelines/new');

        // Fill in the form
        await page.selectOption('select[name="channel_id"]', 'test-channel');
        await page.fill('input[name="topic"]', 'Test Topic');

        // Submit
        await page.click('button[type="submit"]');

        // Should redirect to detail page
        await page.waitForURL(`**/pipelines/${MOCK_RUN_ID}`);

        // Pending badge should be visible
        await expect(page.getByText('Pending')).toBeVisible();
    });
});
