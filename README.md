# arxiv-mcpserver

An MCP (Model Context Protocol) server that provides tools for searching and retrieving academic papers from arXiv.org.

## What it does

This server gives AI agents access to arXiv through 8 specialized tools:

- **arxiv_search** - General keyword search
- **arxiv_search_advanced** - Advanced queries with Boolean operators and field prefixes
- **arxiv_search_by_author** - Find papers by specific author
- **arxiv_search_by_category** - Browse papers by subject category
- **arxiv_get_paper** - Retrieve papers by arXiv ID
- **arxiv_get_latest** - Get newest papers in a category
- **arxiv_get_pdf_url** - Get direct PDF download link
- **arxiv_list_categories** - Browse the complete arXiv subject taxonomy

All tools support dual output formats (JSON for machines, Markdown for humans) and include proper input validation, rate limiting, and caching.

## Installation

```bash
# Clone the repository
git clone https://github.com/rivaldofwijaya/arxiv-mcpserver.git
cd arxiv-mcpserver

# Install the package
pip install .
```

Or with a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"    # editable install with the dev tools
```

Installing the package puts an `arxiv-mcpserver` command on your PATH. If you
would rather not install anything, `pip install -r requirements.txt` and run the
server with `PYTHONPATH=src python -m arxiv_mcp`.

## Usage with AI Agents

### Claude Desktop

Add this to your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "arxiv-mcpserver": {
      "command": "arxiv-mcpserver"
    }
  }
}
```

If you did not install the package, point at the module instead:

```json
{
  "mcpServers": {
    "arxiv-mcpserver": {
      "command": "python",
      "args": ["-m", "arxiv_mcp"],
      "env": {"PYTHONPATH": "/absolute/path/to/arxiv-mcp/src"}
    }
  }
}
```

### Claude Code / OpenCode / OpenClaw

Add the same configuration to your MCP settings:

```json
{
  "mcpServers": {
    "arxiv-mcpserver": {
      "command": "arxiv-mcpserver"
    }
  }
}
```

If you did not install the package, point at the module instead:

```json
{
  "mcpServers": {
    "arxiv-mcpserver": {
      "command": "python",
      "args": ["-m", "arxiv_mcp"],
      "env": {"PYTHONPATH": "/absolute/path/to/arxiv-mcp/src"}
    }
  }
}
```

### Codex

Configure your Codex MCP settings to include the arXiv server:

```json
{
  "mcpServers": {
    "arxiv-mcpserver": {
      "command": "arxiv-mcpserver"
    }
  }
}
```

### Testing with MCP Inspector

For development and testing, you can use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector arxiv-mcpserver
```

## Features

- **Rate Limiting**: Automatically enforces arXiv's 3-second request interval
- **Caching**: 24-hour cache to reduce redundant API calls
- **Dual Formats**: JSON (complete data) and Markdown (human-readable)
- **Validation**: Pydantic models validate all inputs
- **Error Handling**: Clear, actionable error messages

## Example Usage

Once connected to your AI agent, you can:

```
Search for "transformer attention mechanism" papers
Find papers by Geoffrey Hinton
Get the latest papers in cs.LG
Retrieve paper 1706.03762 with full metadata
List all available arXiv categories
```

## Configuration

Optional environment variables:

```bash
export ARXIV_RATE_LIMIT_DELAY=3.0    # Override rate limit (seconds)
export ARXIV_CACHE_EXPIRY=86400      # Override cache duration (seconds)
```

## Available Tools

### 1. arxiv_search
General search across all arXiv fields.

```json
{"query": "neural networks", "max_results": 10}
```

### 2. arxiv_search_advanced
Use Boolean operators and field prefixes.

```json
{
  "query": "au:\"Geoffrey Hinton\" AND cat:stat.ML",
  "max_results": 20
}
```

Supported prefixes: `ti` (title), `au` (author), `abs` (abstract), `cat` (category), `all` (allfields)
Boolean operators: `AND`, `OR`, `ANDNOT`

### 3. arxiv_search_by_author
Find papers by author with optional filters.

```json
{
  "author_name": "Geoffrey Hinton",
  "category": "stat.ML",
  "start_date": "202001010000",
  "end_date": "202212312359",
  "max_results": 15
}
```

### 4. arxiv_search_by_category
Browse papers in a category.

```json
{"category": "cs.AI", "max_results": 20}
```

### 5. arxiv_get_paper
Retrieve papers by arXiv ID.

```json
{"id_list": ["1706.03762", "1810.04805v1"]}
```

### 6. arxiv_get_latest
Get newest papers in a category.

```json
{"category": "cs.LG", "max_results": 10}
```

### 7. arxiv_get_pdf_url
Get PDF download link.

```json
{"paper_id": "1706.03762"}
```

### 8. arxiv_list_categories
Get complete arXiv taxonomy.

```json
{}
```

## Pagination

For many results, use pagination:

```json
// First page
{"query": "machine learning", "start": 0, "max_results": 10}

// Second page
{"query": "machine learning", "start": 10, "max_results": 10}
```

## Date Filtering

Use format `YYYYMMDDHHMM` (24-hour time, GMT):

```json
{
  "query": "quantum computing",
  "start_date": "202301010000",
  "end_date": "202312312359"
}
```

arXiv only supports bounded `submittedDate` ranges, so `start_date` and
`end_date` must be supplied together. Passing just one (or a `start_date` later
than `end_date`) is rejected with a validation error rather than silently
returning unfiltered results.

## Response Formats

All tools support either `json` (complete data) or `markdown` (human-readable).

```json
{"query": "transformer", "response_format": "json"}
{"query": "transformer", "response_format": "markdown"}
```

## Output Fields

Each paper includes: ID, title, summary/abstract, authors, published date, updated date, primary category, all categories, journal reference (if published), DOI (if available), and URLs for abstract and PDF pages.

## Testing

Run the test suite (exits non-zero on failure, so it is safe to gate CI on):

```bash
python tests/test_server_local.py
```

Or through pytest, which picks up `src/` from `pyproject.toml`:

```bash
pytest
```

Lint and type-check the same way CI does:

```bash
ruff check src tests scripts
black --check src tests scripts
mypy src
```

These currently report pre-existing formatting and typing issues, so CI runs
them as advisory steps rather than gates.

Run the evaluation harness against a model via OpenRouter:

```bash
pip install -r scripts/requirements.txt

# stdio transport
python scripts/evaluation.py scripts/example_evaluation.xml \
  -m anthropic/claude-sonnet-4.5 -c arxiv-mcpserver

# sse / http transports
python scripts/evaluation.py scripts/example_evaluation.xml \
  -m anthropic/claude-sonnet-4.5 -t http -u https://your-server/mcp -H "Authorization=Bearer TOKEN"
```

Each task is bounded by `--max-tool-rounds` (default 10) and `--task-timeout`
seconds (default 300); exceeding either records the task as failed instead of
looping indefinitely.

## Rate Limiting & Caching

- **Rate Limiting**: Enforces arXiv's 3-second delay between requests
- **Caching**: 24-hour cache reduces redundant API calls
- **Freshness**: `arxiv_get_latest` accepts cached results only if under 5 minutes old, so it never replays a day-old view of a category
- **Compliance**: Uses HTTPS endpoint and respects arXiv Terms of Use

## Project Structure

```
arxiv-mcp/
├── src/
│   └── arxiv_mcp/
│       ├── __init__.py            # Public API re-exports
│       ├── __main__.py            # `python -m arxiv_mcp`
│       └── server.py              # Main MCP server
├── tests/
│   └── test_server_local.py       # Test suite
├── scripts/
│   ├── evaluation.py              # Evaluation harness
│   ├── connections.py             # MCP utilities
│   ├── requirements.txt           # Harness dependencies
│   └── example_evaluation.xml     # Example tests
├── docs/                          # Long-form documentation
├── examples/                      # Usage examples
├── tools/                         # Developer tooling
├── reports/                       # Generated reports (evaluation output)
├── dist/                          # Build artifacts (untracked)
├── .github/                       # CI, security, issue and PR templates
├── pyproject.toml                 # Project metadata and tool config
├── requirements.txt               # Runtime dependencies
├── SECURITY.md                    # Security policy
├── LICENSE                        # MIT License
└── README.md                      # This file
```

## Dependencies

Core: `mcp[cli]` (2.x), `httpx`, `pydantic`, `feedparser`

For evaluation: `openai`, `mcp` (see `scripts/requirements.txt`)

Built on the mcp 2.x `MCPServer` API (`mcp.server.mcpserver`). mcp 1.x is not
supported, since it predates that module.

## Known Issues

**Author name matching**: Results may vary depending on name format. Try variations:
- Full name: "Geoffrey Hinton"
- With initials: "G. Hinton"
- Last name only: "Hinton"

## Contributing

Issue and pull request templates live in `.github/`. CI runs ruff, black, mypy,
a build check, and the test suite on Python 3.9-3.13.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/name`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/name`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details. To report a security issue,
see [SECURITY.md](SECURITY.md).

When using this server with arXiv data, also comply with:
- arXiv API Terms of Use
- CC BY-SA 4.0 License (for arXiv content)

## Resources

- [arXiv API Documentation](https://info.arxiv.org/help/api/user-manual.html)
- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

**Created by [rivaldofwijaya](https://github.com/rivaldofwijaya)**