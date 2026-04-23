# .governance Directory

This directory stores governance runtime artifacts.

Committed by default:
- `templates/`: reusable templates

Generated at runtime (ignored by git):
- `index/`: lifecycle pointers and maintenance status
- `changes/`: active change packages
- `archive/`: archived change packages
- `runtime/`: optional status/timeline outputs

Use `ocw --root <project> init` to bootstrap generated subdirectories.
