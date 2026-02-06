# Dashboard API Contract (P6-2)

**Version:** 1.0
**Status:** Draft
**Base URL:** `/api/v1`

## Overview
This document defines the API endpoints required for the Web Dashboard functionality.

## 1. Dashboard

### 1.1 Get Dashboard Summary
Retrieves aggregate statistics and recent pipeline activity.

- **Endpoint:** `GET /dashboard/summary`
- **Auth:** Required (API Key)
- **Response:** `200 OK`
```json
{
  "total_runs": 12,
  "active_runs": 2,
  "success_runs": 8,
  "failed_runs": 2,
  "avg_duration_sec": 450,
  "estimated_cost_usd": 0.15,
  "recent_runs": [
    {
      "run_id": "uuid-1234",
      "topic": "Top 10 AI Tools",
      "status": "completed",
      "created_at": "2024-02-06T10:00:00Z"
    }
  ]
}
```

## 2. Pipelines

### 2.1 Get Pipeline Details
Retrieves full details of a specific pipeline run, including status logs and artifacts.

- **Endpoint:** `GET /pipeline/runs/{run_id}`
- **Auth:** Required
- **Response:** `200 OK`
```json
{
  "run_id": "uuid-1234",
  "channel_id": "UC123...",
  "topic": "Top 10 AI Tools",
  "status": "running",
  "current_agent": "script_writer",
  "dry_run": false,
  "created_at": "2024-02-06T10:00:00Z",
  "updated_at": "2024-02-06T10:05:00Z",
  "result": {
    "script": "...",
    "video_url": "..."
  },
  "errors": []
}
```

### 2.2 Create Pipeline Run
Triggers a new pipeline execution.

- **Endpoint:** `POST /pipeline/run`
- **Auth:** Required
- **Body:**
```json
{
  "channel_id": "UC123...",
  "topic": "Future of AI",
  "style": "informative"
}
```
- **Response:** `201 Created`
```json
{
  "run_id": "uuid-new-1234",
  "status": "pending"
}
```

## 3. Channels & Settings

### 3.1 List Channels
- **Endpoint:** `GET /channels`
- **Response:** List of registered channels with status.

### 3.2 List API Keys (Admin)
- **Endpoint:** `GET /admin/api-keys`
- **Response:** List of active API keys.
