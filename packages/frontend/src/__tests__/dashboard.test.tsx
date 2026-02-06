import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Home from '../app/page';
import * as apiModule from '../lib/api';

// Mock the API module
vi.mock('../lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
  API_BASE_URL: 'http://localhost:8000/api/v1',
  ApiError: class extends Error {
    constructor(public status: number, message: string) {
      super(message);
    }
  },
}));

const mockedApi = apiModule.api as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockedApi.get.mockReturnValue(new Promise(() => {})); // Never resolves

    renderWithProviders(<Home />);

    // Should show loading skeleton
    const loadingElements = document.querySelectorAll('.animate-pulse');
    expect(loadingElements.length).toBeGreaterThan(0);
  });

  it('renders dashboard with summary data', async () => {
    mockedApi.get.mockResolvedValue({
      total_runs: 10,
      active_runs: 2,
      success_runs: 7,
      failed_runs: 1,
      avg_duration_sec: 300,
      recent_runs: [
        {
          run_id: 'test-123',
          channel_id: 'tech-channel',
          topic: 'AI Tools',
          status: 'completed',
          dry_run: false,
          created_at: '2026-02-06T10:00:00Z',
          completed_at: '2026-02-06T10:05:00Z',
        },
      ],
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument(); // total_runs
      expect(screen.getByText('2')).toBeInTheDocument(); // active_runs
      expect(screen.getByText('7')).toBeInTheDocument(); // success_runs
      expect(screen.getByText('1')).toBeInTheDocument(); // failed_runs
    });

    expect(screen.getByText('AI Tools')).toBeInTheDocument();
  });

  it('renders empty state when no runs exist', async () => {
    mockedApi.get.mockResolvedValue({
      total_runs: 0,
      active_runs: 0,
      success_runs: 0,
      failed_runs: 0,
      avg_duration_sec: null,
      recent_runs: [],
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText('No recent activity. Start your first pipeline!')).toBeInTheDocument();
    });
  });

  it('renders Create Pipeline button', async () => {
    mockedApi.get.mockResolvedValue({
      total_runs: 0,
      active_runs: 0,
      success_runs: 0,
      failed_runs: 0,
      avg_duration_sec: null,
      recent_runs: [],
    });

    renderWithProviders(<Home />);

    await waitFor(() => {
      expect(screen.getByText('Create Pipeline')).toBeInTheDocument();
    });
  });
});
