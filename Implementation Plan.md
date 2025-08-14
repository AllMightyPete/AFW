# Implementation Plan

## Purpose
This plan translates the conceptual project plans into actionable development milestones. It is a living document and will be updated as the project evolves. After each milestone, schedule a review with stakeholders to validate the direction and refine subsequent tasks.

## Milestone 0 – Project Scaffolding
**Goal:** establish a portable, tested Python project that can grow into the full Asset Organiser.

### Tasks
- Initialise Python package structure:
  - `src/asset_organiser/` for application code.
  - `tests/` for automated tests.
  - `resources/` for UI assets (icons, qml, etc.).
- Add `pyproject.toml` with dependencies (PySide6, pydantic, pytest, etc.).
- Configure virtual environment and tooling (`pre-commit`, `black`, `flake8`, `isort`).
- Set up `pytest` as testing framework and run it in CI.
- Create example config files:
  - `config/settings.json` for application-level configuration.
  - `.asset-library/config.json` for library-level configuration.

### Review
Confirm repository layout, verify tests and linters run in CI, and agree on initial coding conventions.

**Status:** Review completed and milestone approved.

## Milestone 1 – ConfigService
**Goal:** provide read/write access to configuration with validation for use by other services.

### Tasks
- Define configuration models (pydantic or dataclasses) matching **Asset System – Configuration**.
- Implement `ConfigService` with operations:
  - load application settings from disk (with defaults on first run).
  - save modified settings.
  - expose library configuration based on active library path.
  - validate changes and surface errors to UI.
- Add unit tests for happy‑path and failure cases.
- Provide minimal command-line interface or logging hooks for debugging.

### Review
Demonstrate configuration editing round‑trip and validate schema coverage.

## Milestone 2 – PySide6 UI Skeleton
**Goal:** single-window application with sidebar navigation and placeholders for core workflows.

### Tasks
- Create `MainWindow` with sidebar tabs: **Workspace**, **Library**, **Settings**.
- In Workspace view, implement drag‑and‑drop area and stubbed "Unified Asset Tree" widget.
- In Settings view, connect widgets to `ConfigService` for basic read/write of general settings.
- Library view: placeholder grid and metadata panel for future indexing work.
- Implement application entry point (`python -m asset_organiser`).
- Add integration tests or Qt test harness to ensure window loads and basic interactions work.

### Review
Validate look & feel against the UI Interaction plan and confirm configuration edits flow through the UI.

## Milestone 3 – ClassificationService
**Goal:** automated enrichment of source data into structured asset descriptions.

### Tasks
- Define modular pipeline (rule-based and LLM-based modules) as in **Asset System – Classification Service**.
- Implement rule-based file-type detection using keywords from configuration.
- Provide hooks for optional LLM classification; encapsulate API calls for testability.
- Deliver initial unit tests for classification modules using sample inputs.
- Integrate service with Workspace view to classify loaded sources.

### Review
Assess classification accuracy on sample archives and adjust pipeline or configuration schema as needed.

## Milestone 4 – ProcessingService
**Goal:** transform approved assets into final library structure according to configuration.

### Tasks
- Implement processing plan generator and execution engine described in **Asset System – Processor**.
- Support core operations: archive extraction, renaming, resizing, normal map correction, gloss-to-rough inversion, channel packing, metadata generation.
- Add process logging and error reporting back to UI.
- Expand tests to cover plan generation and at least one end‑to‑end processing scenario.

### Review
Run processing on test assets, verify output matches naming conventions and metadata schema.

## Milestone 5 – IndexingService (Optional)
**Goal:** enable semantic search over processed assets.

### Tasks
- Implement optional service to generate embeddings and store them in `.asset-library/index.db`.
- Provide API for text search and thumbnail retrieval.
- Integrate search bar in Library view when indexing is enabled.
- Write tests using a lightweight embedding model to keep CI fast.

### Review
Evaluate indexing performance and search relevance; decide on model choice and default settings.

## Maintenance & Documentation
- Update this plan and project documentation as features mature.
- Maintain changelog and migration notes for configuration or metadata schema updates.
- Continuously refine testing and CI workflows as services evolve.

