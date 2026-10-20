# ai-workforce

Tools and a small Astro site for an AI workforce portfolio. This repo holds the
shared tooling (repo hygiene checks, validators) and the portfolio site.

The individual projects live in separate repos; this repo only links to them.

## Development

```
python -m venv .venv
.venv/Scripts/python -m pip install pytest pyyaml
.venv/Scripts/python -m pytest
.venv/Scripts/python -m tools.hygiene
```

Runtime code uses the Python 3.12 standard library only. No secrets are
committed; copy `.env.example` to `.env` for local settings.

## Workforce

How the four-role workforce operates (roles, loop, commit trailers, handoff log, approval
gates) is in [docs/workforce.md](docs/workforce.md). The design behind it is in
[docs/superpowers/specs/2026-10-19-ai-workforce-portfolio-design.md](docs/superpowers/specs/2026-10-19-ai-workforce-portfolio-design.md).
