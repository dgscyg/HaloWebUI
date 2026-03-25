# HaloWebUI build and compile commands

This repository's local workflow is based on **Node 22** and the repo-local **`.venv`** created by `uv sync --frozen`.

## Environment setup

Run these commands before local build or validation work:

```bash
source /home/dragon/.nvm/nvm.sh
nvm use 22
cd /data/other/HaloWebUI
uv sync --frozen
```

- `nvm use 22` matches the repo's supported Node engine range and mission runtime guidance.
- `uv sync --frozen` creates or updates `.venv` for backend Python commands.

## Core local commands

### Frontend dev server

```bash
source /home/dragon/.nvm/nvm.sh && nvm use 22 >/dev/null
cd /data/other/HaloWebUI
npm run dev
```

### Frontend build

```bash
source /home/dragon/.nvm/nvm.sh && nvm use 22 >/dev/null
cd /data/other/HaloWebUI
npm run build
```

### Frontend type check

```bash
source /home/dragon/.nvm/nvm.sh && nvm use 22 >/dev/null
cd /data/other/HaloWebUI
npm run check
```

### Frontend tests

```bash
source /home/dragon/.nvm/nvm.sh && nvm use 22 >/dev/null
cd /data/other/HaloWebUI
npx vitest run
```

### Backend targeted tests used in this mission

```bash
cd /data/other/HaloWebUI/backend
../.venv/bin/python -m pytest open_webui/test/unit/test_mcp.py -q
```

## Makefile shortcuts

The repository keeps the existing Docker lifecycle targets and now also exposes local workflow helpers:

```bash
make local-setup    # uv sync --frozen with Node 22 selected
make build          # npm run build
make build-full     # npm run build:full
make build-debug    # npm run build:debug
make check          # npm run check
make test           # vitest + backend targeted pytest
make test-frontend  # vitest only
make validate       # test, then npm run build
```

## Notes

- `npm run build` is the main compile/build command and is the one smoke-tested for this workflow update.
- `npm run check` is the repo's frontend type-check command; broader repo noise may still exist outside the files touched by a given mission, so use mission-scoped typecheck expectations when applicable.
- The Makefile's original Docker-oriented targets (`install`, `start`, `startAndBuild`, `stop`, `remove`, `update`) remain available.
