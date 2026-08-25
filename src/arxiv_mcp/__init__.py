'''MCP server for searching and retrieving academic papers from arXiv.org.'''

from arxiv_mcp.server import (
    ERROR_PREFIX,
    ArxivAuthorSearchInput,
    ArxivCategorySearchInput,
    ArxivGetPaperInput,
    ArxivGetPdfUrlInput,
    ArxivSearchInput,
    ResponseFormat,
    SortBy,
    SortOrder,
    arxiv_get_latest,
    arxiv_get_paper,
    arxiv_get_pdf_url,
    arxiv_list_categories,
    arxiv_search,
    arxiv_search_advanced,
    arxiv_search_by_author,
    arxiv_search_by_category,
    main,
    mcp,
)

__version__ = "2.0.0"

__all__ = [
    "ERROR_PREFIX",
    "ArxivAuthorSearchInput",
    "ArxivCategorySearchInput",
    "ArxivGetPaperInput",
    "ArxivGetPdfUrlInput",
    "ArxivSearchInput",
    "ResponseFormat",
    "SortBy",
    "SortOrder",
    "__version__",
    "arxiv_get_latest",
    "arxiv_get_paper",
    "arxiv_get_pdf_url",
    "arxiv_list_categories",
    "arxiv_search",
    "arxiv_search_advanced",
    "arxiv_search_by_author",
    "arxiv_search_by_category",
    "main",
    "mcp",
]
