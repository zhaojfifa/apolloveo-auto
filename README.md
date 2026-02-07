# apolloveo-auto

This repo is the clean baseline for ApolloVeo V1.9+ evolution, oriented for **collaboration** and **2.0 pluginization**.

## Three scenarios (v1.9 baseline)
1. **Mainline**: parse → subtitles/translation → dubbing → pack (CapCut/YouCut deliverables)
2. **Avatar**: image-driven avatar pipeline + publish hub
3. **Hot Follow**: trend discovery → selection → enter production pipeline

## Repo map
- gateway/ : backend service (single entrypoint: gateway/main.py → gateway/app/main.py)
- docs/ : baseline, runbooks, architecture, skills (team knowledge)
- ops/ : checks + scripts
- assets/ : accumulated reusable assets (B-roll / avatar / hot-follow)

## Quick commands
- Core import smoke test:
  - powershell -ExecutionPolicy Bypass -File ops/checks/check_import_app.ps1

> Rules: docs + skills are first-class. Any workflow/policy change must be reflected in docs.
