# Packages Directory

This directory contains the independent components of the Youtube AI Agent Agency.
We are transitioning to a workspace-based architecture.

## Current Packages
- **agents**: The core agent logic (Legacy Monolith).

## Future Packages (Planned)
- **brand_researcher**: Isolated brand research agent.
- **script_writer**: Isolated script writing agent.
- **frontend**: Next.js Web Dashboard.
- **core**: Shared utilities and models.

## Development
Each package can be developed and tested independently.
Use `uv run --package [package_name] [command]` to run commands in a specific package context.
