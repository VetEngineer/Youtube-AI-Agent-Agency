# Dashboard API Contract (P6-2)

**Version:** 1.1
**Status:** Implemented
**Base URL:** `/api/v1`
**Auth:** All endpoints require `X-API-Key` header (except `/health`)

## Overview

This document defines the API endpoints required for the Web Dashboard functionality.

---

## 1. Dashboard

### 1.1 Get Dashboard Summary

Retrieves aggregate statistics and recent pipeline activity.

- **Endpoint:** `GET /dashboard/summary`
- **Auth:** Required (`require_api_key`)
- **Query Parameters:**
  | Parameter | Type | Default | Description |
  |-----------|------|---------|-------------|
  | `limit` | int | 5 | Number of recent runs to return |

- **Response:** `200 OK`

```json
{
  "total_runs": 12,
  "active_runs": 2,
  "success_runs": 8,
  "failed_runs": 2,
  "avg_duration_sec": 450.5,
  "estimated_cost_usd": null,
  "recent_runs": [
    {
      "run_id": "550e8400-e29b-41d4-a716-446655440000",
      "channel_id": "tech-channel",
      "topic": "Top 10 AI Tools",
      "status": "completed",
      "dry_run": false,
      "created_at": "2026-02-06T10:00:00Z",
      "completed_at": "2026-02-06T10:15:00Z"
    }
  ]
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total_runs` | int | Total number of pipeline runs |
| `active_runs` | int | Running pipelines (pending + running) |
| `success_runs` | int | Completed successfully |
| `failed_runs` | int | Failed runs |
| `avg_duration_sec` | float \| null | Average completion time in seconds |
| `estimated_cost_usd` | float \| null | Estimated cost (null until P8-3) |
| `recent_runs` | array | Recent pipeline runs |

---

## 2. Pipelines

### 2.1 List Pipeline Runs

Retrieves paginated list of pipeline runs with optional filtering.

- **Endpoint:** `GET /pipeline/runs`
- **Auth:** Required
- **Query Parameters:**
  | Parameter | Type | Default | Description |
  |-----------|------|---------|-------------|
  | `channel_id` | string | null | Filter by channel |
  | `status` | string | null | Filter by status |
  | `limit` | int | 20 | Page size (1-100) |
  | `offset` | int | 0 | Pagination offset |

- **Response:** `200 OK`

```json
{
  "runs": [
    {
      "run_id": "550e8400-e29b-41d4-a716-446655440000",
      "channel_id": "tech-channel",
      "topic": "AI Trends 2026",
      "status": "completed",
      "dry_run": false,
      "created_at": "2026-02-06T10:00:00Z",
      "completed_at": "2026-02-06T10:15:00Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### 2.2 Get Pipeline Run Details

Retrieves full details of a specific pipeline run.

- **Endpoint:** `GET /pipeline/runs/{run_id}`
- **Auth:** Required
- **Path Parameters:**
  | Parameter | Type | Description |
  |-----------|------|-------------|
  | `run_id` | string | Pipeline run UUID |

- **Response:** `200 OK`

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "channel_id": "tech-channel",
  "topic": "Top 10 AI Tools",
  "brand_name": "TechReview",
  "status": "running",
  "current_agent": "script_writer",
  "dry_run": false,
  "created_at": "2026-02-06T10:00:00Z",
  "updated_at": "2026-02-06T10:05:00Z",
  "completed_at": null,
  "result": null,
  "errors": []
}
```

- **Response:** `404 Not Found`

```json
{
  "detail": "파이프라인 실행을 찾을 수 없습니다"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique run identifier |
| `channel_id` | string | Target channel ID |
| `topic` | string | Content topic |
| `brand_name` | string | Brand name (optional) |
| `status` | string | pending \| running \| completed \| failed |
| `current_agent` | string \| null | Currently executing agent |
| `dry_run` | boolean | Skip actual upload |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | Last update timestamp |
| `completed_at` | string \| null | Completion timestamp |
| `result` | object \| null | Pipeline output |
| `errors` | array | Error messages |

### 2.3 Create Pipeline Run

Triggers a new pipeline execution.

- **Endpoint:** `POST /pipeline/run`
- **Auth:** Required
- **Body:**

```json
{
  "channel_id": "tech-channel",
  "topic": "Future of AI",
  "brand_name": "TechReview",
  "dry_run": false
}
```

- **Response:** `200 OK`

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "channel_id": "tech-channel",
  "topic": "Future of AI"
}
```

---

## 3. Status

### 3.1 Get Pipeline Status (Legacy)

- **Endpoint:** `GET /status/{run_id}`
- **Auth:** Required
- **Note:** Use `GET /pipeline/runs/{run_id}` for more details

- **Response:** `200 OK`

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "current_agent": "script_writer",
  "errors": [],
  "result": null
}
```

### 3.2 Health Check

- **Endpoint:** `GET /health`
- **Auth:** Not required
- **Response:** `200 OK`

```json
{
  "status": "healthy"
}
```

---

## 4. Channels

### 4.1 List Channels

- **Endpoint:** `GET /channels/`
- **Auth:** Required
- **Response:** `200 OK`

```json
{
  "channels": [
    {
      "channel_id": "tech-channel",
      "name": "Tech Review",
      "category": "technology",
      "has_brand_guide": true
    }
  ],
  "total": 1
}
```

### 4.2 Get Channel

- **Endpoint:** `GET /channels/{channel_id}`
- **Auth:** Required

### 4.3 Create Channel

- **Endpoint:** `POST /channels/`
- **Auth:** Required (admin scope)

### 4.4 Update Channel

- **Endpoint:** `PATCH /channels/{channel_id}`
- **Auth:** Required (admin scope)

### 4.5 Delete Channel

- **Endpoint:** `DELETE /channels/{channel_id}`
- **Auth:** Required (admin scope)

---

## 5. Admin

### 5.1 List API Keys

- **Endpoint:** `GET /admin/api-keys`
- **Auth:** Required (admin scope)

### 5.2 Create API Key

- **Endpoint:** `POST /admin/api-keys`
- **Auth:** Required (admin scope)

### 5.3 Delete API Key

- **Endpoint:** `DELETE /admin/api-keys/{key_id}`
- **Auth:** Required (admin scope)

### 5.4 List Audit Logs

- **Endpoint:** `GET /admin/audit-logs`
- **Auth:** Required (admin scope)

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message here"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## OpenAPI

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
