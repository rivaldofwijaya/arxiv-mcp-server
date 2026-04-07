# arXiv MCP Server

[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue)](https://modelcontextprotocol.io/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Production-ready MCP server for searching and retrieving academic papers from arXiv.org via the official arXiv API.

---

## Table of Contents

- [Overview](#overview)
- [Why arXiv MCP Server?](#why-arxiv-mcp-server)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [Pagination](#pagination)
- [Date Filtering](#date-filtering)
- [Response Formats](#response-formats)
- [Testing](#testing)
- [Rate Limiting & Caching](#rate-limiting--caching)
- [ArXiv API Compliance](#arxiv-api-compliance)
- [Error Handling](#error-handling)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Development](#development)
- [Known Issues](#known-issues)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [References](#references)

## Overview

This server provides 8 specialized tools that enable AI agents to seamlessly interact with the arXiv repository:

- **Full-text search** with advanced query syntax
- **Author-specific searches** with category filtering
- **Category browsing** for discovering papers
- **Paper retrieval** by arXiv ID
- **Date range filtering** for temporal queries
- **Complete taxonomy access** for all arXiv categories

All tools follow MCP best practices with proper annotations, input validation, and dual output formats (JSON/Markdown).

## Why arXiv MCP Server?

- **Production-Ready**: Battle-tested with comprehensive error handling and rate limiting
- **MCP-Native**: Built specifically for the Model Context Protocol with full tool annotations
- **Developer-Friendly**: Clear documentation, dual output formats, and extensive examples
- **API-Compliant**: Respects arXiv's rate limits and terms of service
- **Well-Maintained**: Active development with proper testing and evaluation suites

## Features

✅ **Comprehensive Tool Coverage**: 8 specialized tools for different search patterns  
✅ **Rate Limiting**: Compliant with arXiv's 3-second request interval  
✅ **Response Caching**: 24-hour cache for improved performance  
✅ **Dual Output Formats**: JSON (machine-readable) and Markdown (human-readable)  
✅ **Input Validation**: Pydantic models with comprehensive constraints  
✅ **Error Handling**: Specific, actionable error messages with guidance  
✅ **ArXiv API Compliance**: Full support for Boolean operators, field prefixes, and date filtering  

## Quick Start

Get started in 3 simple steps:

```bash
# 1. Clone the repository
git clone https://github.com/rivaldofwijaya/arxiv-mcp-server.git
cd arxiv-mcp-server

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
python server.py
```

For use with Claude Desktop or other MCP clients, see [Usage](#usage) below.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download this repository**

```bash
git clone https://github.com/rivaldofwijaya/arxiv-mcp-server.git
cd arxiv-mcp-server
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

Or using a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Running the Server

**Basic usage (stdio transport)**:
```bash
python server.py
```

**With MCP Inspector** (development/testing):
```bash
npx @modelcontextprotocol/inspector python server.py
```

**As an MCP server in Claude Desktop or other MCP clients**:

Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "arxiv": {
      "command": "python",
      "args": ["/path/to/arxiv-mcp-server/server.py"]
    }
  }
}
```

For Claude Desktop, this configuration file is typically located at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

## Available Tools

### 1. `arxiv_search`
General keyword search across all fields in arXiv.

**When to use**: Broad searches without specific filters (e.g., "transformer attention", "quantum computing").

**Example**:
```json
{
  "query": "neural networks",
  "max_results": 10,
  "response_format": "markdown"
}
```

### 2. `arxiv_search_advanced`
Advanced search with Boolean operators and field prefixes.

**When to use**: Complex queries combining multiple filters (author + category, author + title, etc.).

**Supported prefixes**: `ti` (title), `au` (author), `abs` (abstract), `co` (comment), `jr` (journal ref), `cat` (category), `rn` (report number), `all` (all fields)

**Boolean operators**: `AND`, `OR`, `ANDNOT`

**Examples**:
```json
// Author + Title
{
  "query": "au:\"Geoffrey Hinton\" AND ti:backpropagation",
  "max_results": 5
}

// Category + exclude terms
{
  "query": "cat:cs.AI ANDNOT ti:neural",
  "max_results": 10
}

// Date range in query
{
  "query": "au:\"Geoffrey Hinton\" AND cat:stat.ML AND submittedDate:[202001010000+TO+202212312359]",
  "max_results": 20
}

// Boolean grouping
{
  "query": "au:del_maestro ANDNOT (ti:checkerboard OR ti:Pyrochlore)",
  "max_results": 10
}
```

### 3. `arxiv_search_by_author`
Search papers by specific author with optional category filter.

**When to use**: Finding all papers by an author, optionally within a specific category.

**Example**:
```json
{
  "author_name": "Geoffrey Hinton",
  "category": "stat.ML",
  "start_date": "202001010000",
  "end_date": "202212312359",
  "max_results": 15,
  "sort_by": "submittedDate",
  "sort_order": "descending"
}
```

**Note**: Author name matching can be exact or partial. For better results, try different variations:
- Full name: "Geoffrey Hinton"
- Last name: "Hinton"
- With initials: "G. Hinton"

### 4. `arxiv_search_by_category`
Browse papers within a specific arXiv category.

**When to use**: Exploring a subject area, with optional author filter.

**Example**:
```json
{
  "category": "cs.AI",
  "max_results": 20,
  "sort_by": "submittedDate",
  "sort_order": "descending"
}
```

### 5. `arxiv_get_paper`
Retrieve complete metadata for specific paper(s) by arXiv ID.

**When to use**: When you have the exact arXiv ID(s) and need full details.

**Example**:
```json
{
  "id_list": ["1706.03762", "1810.04805v1"],
  "response_format": "json"
}
```

**Supports version-specific IDs**: Append version number (e.g., `"1706.03762v2"`) to retrieve a specific version.

### 6. `arxiv_get_latest`
Get the most recent submissions in a category (sorted by submission date).

**When to use**: Finding newest papers in a subject area.

**Example**:
```json
{
  "category": "cs.LG",
  "max_results": 10
}
```

### 7. `arxiv_get_pdf_url`
Get the direct PDF download URL for a paper.

**When to use**: When you need the PDF link for an arXiv ID.

**Example**:
```json
{
  "paper_id": "1706.03762"
}
```

Returns: `https://arxiv.org/pdf/1706.03762.pdf`

### 8. `arxiv_list_categories`
Retrieve the complete arXiv subject taxonomy.

**When to use**: Discovering available categories for filtering.

**Example**:
```json
{}
```

Returns a structured taxonomy with category IDs (e.g., `cs.AI`, `stat.ML`) and descriptions.

## Pagination

For searches returning many results, use pagination:

**How it works**:
- Total results shown in response metadata
- Use `start` parameter to skip results (0-based index)
- Set `max_results` to control page size

**Example - Iterating through results**:
```json
// First page
{
  "query": "machine learning",
  "start": 0,
  "max_results": 10
}

// Second page
{
  "query": "machine learning",
  "start": 10,  // Start at result #11
  "max_results": 10
}

// Third page
{
  "query": "machine learning",
  "start": 20,
  "max_results": 10
}
```

**Maximum page size**: 100 for author/category searches, 2000 for general searches (keeps responses manageable).

## Date Filtering

Date ranges use the format `YYYYMMDDHHMM` (24-hour time, GMT).

**Examples**:
- `202001010000` - January 1, 2020, 00:00 GMT
- `202212312359` - December 31, 2022, 23:59 GMT

**Usage**:
```json
{
  "query": "quantum computing",
  "start_date": "202301010000",
  "end_date": "202312312359"
}
```

## Response Formats

All search tools support two output formats:

### Markdown (default)
Human-readable format with:
- Clear headers and structure
- Truncated abstracts (600 characters)
- Formatted author list with affiliations
- Direct links to abstract and PDF

### JSON
Machine-readable structured data with:
- Complete metadata (no truncation)
- Full abstract text
- Detailed author information
- Structured pagination info

**Example**:
```json
{
  "query": "transformer",
  "response_format": "json"
}
```

### Output Fields

Each paper result includes:
- **id**: arXiv ID (with version if specified)
- **title**: Paper title
- **summary**: Abstract (Markdown: truncated; JSON: full)
- **authors**: List of author names
- **authors_detailed**: Authors with affiliations (JSON only)
- **published**: Initial submission date
- **updated**: Last update date
- **primary_category**: Main subject classification
- **categories**: All subject classifications
- **comment**: Author comments (if provided)
- **journal_ref**: Journal reference (if published)
- **doi**: DOI link (if available)
- **abs_url**: Abstract page URL
- **pdf_url**: PDF download URL

## Testing

### Local Testing

Run the test suite:
```bash
python scripts/test_server_local.py
```

This tests:
- Basic search functionality
- Advanced Boolean queries
- Paper retrieval by ID
- Rate limiting and caching
- Category listing

### Evaluation Testing

Run the comprehensive evaluation with an LLM:
```bash
python scripts/evaluation.py \
  -t stdio \
  -c python \
  -a server.py \
  -m anthropic/claude-3.5-sonnet \
  scripts/example_evaluation.xml
```

**Requirements**:
- OpenRouter API key: `export OPENROUTER_API_KEY=your_key`

## Rate Limiting & Caching

### Rate Limiting

This server enforces arXiv's recommended 3-second delay between requests:
- Implemented as an async-friendly rate limiter
- Applies to all API calls automatically
- Logs when waiting is required

**Configuration** (optional):
```bash
export ARXIV_RATE_LIMIT_DELAY=3.0  # Override default
```

### Caching

Results are cached for 24 hours:
- Reduces redundant API calls
- Improves response times for repeated queries
- Cache key includes all query parameters

**Configuration** (optional):
```bash
export ARXIV_CACHE_EXPIRY=86400  # Override (seconds)
```

## ArXiv API Compliance

This server respects arXiv's Terms of Use:

- ✅ 3-second delay between requests
- ✅ Maximum 2000 results per request
- ✅ HTTPS endpoint used
- ✅ No authentication required (public API)
- ✅ Proper query encoding

**ArXiv API limits**:
- Max 30,000 results per session
- Max 2000 results per single request
- Rate limit: 3 seconds between requests

## Error Handling

The server provides specific, actionable error messages:

- **HTTP 400**: Invalid query syntax with guidance on fixing it
- **HTTP 403**: Access forbidden (VPN/proxy issues)
- **HTTP 429**: Rate limit exceeded with retry suggestion
- **HTTP 503**: Service unavailable with status check link
- **Timeout**: Request timeout with optimization tips
- **Validation errors**: Clear messages about invalid parameters

## Project Structure

```
arxiv-mcp-server/
├── server.py                      # Main MCP server implementation
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── LICENSE                        # MIT License
├── pyproject.toml                 # Project metadata and build config
└── scripts/
    ├── test_server_local.py       # Local test suite
    ├── evaluation.py              # Evaluation harness
    ├── connections.py             # MCP connection utilities
    ├── requirements.txt           # Script dependencies
    └── example_evaluation.xml     # Example evaluation test cases
```

## Dependencies

Core dependencies (see `requirements.txt`):
- `mcp[cli]` - MCP Python SDK
- `httpx` - Async HTTP client
- `pydantic` - Input validation
- `feedparser` - Atom XML parsing

Additional dependencies for evaluation (see `scripts/requirements.txt`):
- `anthropic` - Anthropic API client for LLM evaluation

## Development

### Code Quality

- **Python version**: 3.8+
- **Type hints**: Used throughout
- **Pydantic v2**: Modern validation framework
- **Async/await**: All network operations are async
- **Error handling**: Comprehensive with specific messages

### Running Tests

```bash
# Syntax check
python -m py_compile server.py

# Import check
python -c "from server import mcp; print('OK')"

# Functional tests
python scripts/test_server_local.py
```

## Known Issues

### Author Name Matching

**Issue**: When searching by author name, results may vary depending on the name format used.

**Root cause**: arXiv API's author name matching has variations:
- Some papers use full names, others use initials
- Name formatting inconsistencies across submissions
- Multiple acceptable name formats

**Workaround**: Try multiple author name formats:
- `"Geoffrey Hinton"` (full name)
- `"G. Hinton"` (with initials)
- `"Hinton"` (last name only)

## Contributing

When contributing to this project, please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Guidelines**:
- Maintain backward compatibility
- Add tests for new functionality
- Update documentation
- Follow the existing code style
- Ensure all tests pass

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note**: This project uses the arXiv API. The arXiv data is provided under CC BY-SA 4.0 license. When using this server, please comply with both:
- MIT License (for this software)
- arXiv API Terms of Use
- CC BY-SA 4.0 License (for arXiv content)

## Acknowledgments

- **arXiv.org** for providing the open API and maintaining the academic paper repository
- **Model Context Protocol (MCP)** for the server framework and specifications
- **The academic community** for supporting open access to research

## References

- [arXiv API User Manual](https://info.arxiv.org/help/api/user-manual.html)
- [arXiv API Basics](https://info.arxiv.org/help/api/basics.html)
- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

**Created by [rivaldofwijaya](https://github.com/rivaldofwijaya)**