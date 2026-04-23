# Contributing

Thanks for contributing to open-cowork.

## Development Setup

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

## Contribution Rules

1. Keep governance boundaries explicit.
2. Do not weaken execution/review separation.
3. Add or update tests for behavior changes.
4. Keep docs aligned with actual runtime behavior.
5. Avoid embedding personal local paths or private environment details.

## Pull Request Checklist

- [ ] Tests pass locally
- [ ] Docs updated for user-facing changes
- [ ] No personal-domain secrets or local absolute paths leaked
- [ ] Change remains within bounded scope
