# Contributing to AIG-Doggy

Thank you for your interest in contributing to AIG-Doggy!

## Development Setup

```bash
git clone https://github.com/aicodow/AIG-Doggy.git
cd AIG-Doggy/src
uv sync --group dev
docker compose -f docker-compose.dev.yml up -d
psql -h localhost -U doggy -d doggy -f scripts/init_db.sql
```

## Branch Strategy

- `main` — production releases
- `develop` — integration branch
- `feature/<name>` — new features
- `fix/<name>` — bug fixes

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(rails): add content safety input guardrail
fix(stream): resolve streaming token counting error
docs(api): update OpenAI compatibility docs
test(adapters): add Anthropic adapter unit tests
```

## Pull Request Process

1. Create a feature branch from `develop`
2. Write code with tests (coverage >= 80%)
3. Run `ruff check` and `pytest`
4. Submit PR to `develop`
5. Pass CI checks (lint + type-check + test)
6. Get at least one review approval
7. Squash merge to `develop`

## Code Style

- Python: PEP 8 via `ruff`
- Type hints required for all public APIs
- Docstrings: Google style
- Colang: see `doggy/configs/default/` for examples

## Testing

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Security effectiveness tests
uv run pytest tests/security/ -v

# All tests
uv run pytest tests/ -v
```

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.