# open-cowork

open-cowork is a **Collaboration Governance Runtime**.

It helps people and agents collaborate on complex work with explicit governance boundaries:
- structured change packages
- execution contracts
- evidence-driven verification and review
- archive and continuity handoff

## What This Project Is

open-cowork is a governance layer, not an execution engine.
It is designed to coordinate multiple humans/agents/tools under one bounded lifecycle.

## What This Project Is Not

- not a heavy workflow platform
- not a unified AI coding runtime
- not a toolchain lock-in system

## Repository Layout

- `src/governance/`: governance runtime modules
- `src/adapters/`: execution adapter interface + default adapter
- `bin/ocw`: CLI entrypoint
- `docs/specs/`: design and governance specs
- `.governance/templates/`: reusable governance templates
- `tests/`: unit tests

## Quick Start

### 1. Install

```bash
python3 -m pip install -e .
```

### 2. Initialize governance structure in your project

```bash
ocw --root . init
```

### 3. Check lifecycle status

```bash
ocw --root . status
```

### 4. Diagnose session/context instability (optional)

```bash
ocw --root . diagnose-session
ocw --root . session-recovery-packet
```

## Current CLI Coverage

Implemented now:
- `init`
- `status`
- `diagnose-session`
- `session-recovery-packet`

Planned next:
- `propose`, `change create`, `contract`, `run`, `verify`, `review`, `archive`

## Personal-Domain and Team Adoption

To start quickly in personal domains and team collaboration:
1. Keep your existing repo/toolchain unchanged.
2. Add `open-cowork` as governance layer only.
3. Use `ocw init` to create bounded governance directories.
4. Treat governance artifacts as source of truth for review/archive decisions.

## Documentation

- Project docs index: [`docs/README.md`](docs/README.md)
- Specs: `docs/specs/`
- Recovery playbook: [`docs/reports/02-session-recovery-playbook.md`](docs/reports/02-session-recovery-playbook.md)

## Development

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
