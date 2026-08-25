## Summary

<!-- What does this change and why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature (new tool or new tool parameter)
- [ ] Breaking change (existing tool signature or output changes)
- [ ] Documentation
- [ ] Tooling / CI

## Testing

<!-- How did you verify this? Paste the relevant command output. -->

- [ ] `ruff check src dev/tests dev/scripts` and `black --check src dev/tests dev/scripts` pass
- [ ] `mypy src` passes
- [ ] `python dev/tests/test_server_local.py` passes against the live arXiv API
- [ ] Verified in an MCP client (`npx @modelcontextprotocol/inspector python -m arxiv_mcp`)

## Checklist

- [ ] README updated if tool behavior, arguments, or setup changed
- [ ] No secrets, tokens, or personal data in the diff
- [ ] Change respects the arXiv API Terms of Use (rate limiting, HTTPS endpoint)
