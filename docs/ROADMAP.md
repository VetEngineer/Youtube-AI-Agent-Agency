# Project Roadmap & Architecture Plan

## Overview
This document outlines the future development phases (Phase 6+) and the architectural transition to a modular monorepo to support independent agent development.

## Phase 6: Web Dashboard (Frontend)
**Goal:** Provide a user-friendly web interface for controlling the agency.

### Key Features
- **Dashboard:** View active pipelines, status overview, and recent results.
- **Pipeline Control:** Trigger new video creation (Keyword input, configuration).
- **Result Viewer:** Review generated scripts, images, and video implementation.
- **Settings:** Manage API Keys, Channel Configurations visually.

### Tech Stack
- **Framework:** Next.js (App Router)
- **UI Library:** shadcn/ui + Tailwind CSS
- **State Management:** TanStack Query (React Query)
- **Deployment:** Vercel (Frontend) / Docker (Backend)

## Phase 7: Advanced Architecture & Scalability
**Goal:** Enhance system robustness and support parallel agents.

### Key Features
- **Task Queue:** Implement Redis + Celery/Arq for asynchronous task processing.
- **RAG Implementation:** Enhance `Brand Researcher` with Vector DB (Chroma/Pinecone) for better context.
- **Independent Agent Deployment:** Containerize each agent for independent scaling.

## Phase 8: Production Operations
**Goal:** Ensure stability in production environments.

### Key Features
- **Monitoring:** Prometheus + Grafana dashboard.
- **Centralized Logging:** ELK Stack or Loki.
- **Cost Management:** Tracking API usage per agent/pipeline.

---

## Architecture Refactor: Independent Agent Development Environment
To support "independent development spaces" for multiple agents, we will transition to a **Workspace-based Monorepo**.

### Current Structure
```
packages/agents/src/[agent_name] (Monolithic Package)
```

### Target Structure (UV Workspace)
Each agent becomes an independent Python package with its own dependencies and tests.

```
/
├── pyproject.toml (Workspace Root)
├── uv.lock
├── packages/
│   ├── core/               # Shared models, config, utils
│   ├── api/                # FastAPI Application
│   ├── orchestrator/       # LangGraph Supervisor
│   ├── brand_researcher/   # Independent Agent Package
│   ├── script_writer/      # Independent Agent Package
│   ├── ...
│   └── frontend/           # Next.js Application
└── ...
```

### Benefits
1.  **Isolation:** Changes in `script_writer` don't accidentally break `brand_researcher`.
2.  **Independent Testing:** Run tests for specific agents only.
3.  **Clear Dependencies:** Each agent declares explicitly what it needs.
