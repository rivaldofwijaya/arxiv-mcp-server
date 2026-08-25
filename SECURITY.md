# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 2.x     | Yes       |
| 1.x     | No        |

Version 2.x requires the `mcp` 2.x SDK. The 1.x line is no longer maintained.

## Reporting a vulnerability

Report vulnerabilities privately. Do not open a public issue.

- Preferred: [open a private advisory](https://github.com/rivaldofwijaya/arxiv-mcpserver/security/advisories/new)
  through GitHub's private vulnerability reporting.
- Alternative: email **gandhi+claude@itsecasia.com**.

Please include a description of the issue, the steps or tool arguments needed to
reproduce it, and the affected version. You will get an acknowledgement within 5
business days and a status update at least every 14 days until the report is
resolved. Please give us 90 days before public disclosure.

## Scope

This project is a read-only MCP server. It sends queries to the public arXiv API
over HTTPS and returns the results; it holds no credentials and stores nothing on
disk. Reports that are in scope include:

- Input handling that lets a caller reach an unintended URL or endpoint
  (for example, injection through query, category, or paper-ID parameters).
- Parsing of arXiv responses that can crash the server or produce misleading
  output attributed to arXiv.
- Unbounded resource use in the in-memory cache or rate limiter.
- Vulnerable pinned dependencies.

Out of scope:

- Vulnerabilities in arXiv itself — report those to arXiv.
- Vulnerabilities in the MCP client you use, or in the `mcp` SDK.
- Rate limiting of the arXiv API itself, which is arXiv's policy to set.
- Findings that require an attacker to already control the machine running the
  server or its Python environment.

## Operational notes

The server accepts tool calls from whatever MCP client it is configured in and
trusts that client. Run it only with clients you trust, and remember that all
queries are visible to arXiv.
