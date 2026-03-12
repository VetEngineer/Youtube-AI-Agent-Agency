# Packages Directory

This directory contains the executable components of the Youtube AI Agent Agency.

## Workspace Packages
- **core**: Shared config, models, DB engine, repositories
- **agents**: LangGraph orchestrator and agent implementations
- **api**: FastAPI app, CLI, and Arq worker

## Non-workspace Package
- **frontend**: Next.js dashboard app. Present in the repo, but not included in the root `uv` workspace.

## Development
Each package can be developed and tested independently.
Use `uv run --package [package_name] [command]` to run commands in a specific package context.
