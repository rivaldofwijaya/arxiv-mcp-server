#!/usr/bin/env python3
import asyncio
import logging
import sys
from arxiv_mcp.server import (
    arxiv_search,
    arxiv_get_paper,
    arxiv_list_categories,
    ArxivSearchInput,
    ArxivGetPaperInput,
    ERROR_PREFIX,
    SortBy,
    SortOrder,
    ResponseFormat
)

# Setup basic logging to see the output
logging.basicConfig(level=logging.INFO)

def assert_ok(result: str, context: str):
    """Fail loudly when a tool returns an error string or an empty response."""
    if not result or not result.strip():
        raise AssertionError(f"{context}: empty response")
    if result.startswith(ERROR_PREFIX):
        raise AssertionError(f"{context}: tool returned an error -> {result[:200]}")

async def test_search():
    print("\n--- Testing Basic Search ---")
    params = ArxivSearchInput(query="transformer attention", max_results=2)
    result = await arxiv_search(params)
    assert_ok(result, "basic search")
    print(result[:500] + "...")

async def test_advanced_search():
    print("\n--- Testing Advanced Search (Boolean) ---")
    params = ArxivSearchInput(query="au:\"Yann LeCun\" AND ti:convolutional", max_results=1)
    result = await arxiv_search(params)
    assert_ok(result, "advanced search")
    print(result[:500] + "...")

async def test_get_paper():
    print("\n--- Testing Get Paper by ID ---")
    params = ArxivGetPaperInput(id_list=["1706.03762"]) # Attention is All You Need
    result = await arxiv_get_paper(params)
    assert_ok(result, "get paper")
    if "1706.03762" not in result:
        raise AssertionError("get paper: response does not mention the requested arXiv ID")
    print(result[:500] + "...")

def test_partial_date_range_rejected():
    print("\n--- Testing Partial Date Range Rejection ---")
    rejected_cases = [
        ({"start_date": "202001010000"}, "start_date without end_date"),
        ({"start_date": "202212312359", "end_date": "202001010000"}, "inverted date range"),
    ]
    for kwargs, description in rejected_cases:
        try:
            ArxivSearchInput(query="transformer", **kwargs)
        except ValueError:
            print(f"{description} correctly rejected")
        else:
            raise AssertionError(f"date range validation: {description} was accepted")

async def test_rate_limiting_and_cache():
    print("\n--- Testing Rate Limiting and Cache ---")
    params = ArxivSearchInput(query="quantum computing", max_results=1)

    print("First call (should trigger API fetch and wait if needed):")
    first = await arxiv_search(params)
    assert_ok(first, "cache warm-up call")

    print("\nSecond call (should be INSTANT due to cache):")
    start_time = asyncio.get_event_loop().time()
    second = await arxiv_search(params)
    end_time = asyncio.get_event_loop().time()
    elapsed = end_time - start_time
    assert_ok(second, "cached call")
    print(f"Cache retrieval took: {elapsed:.4f}s")
    if elapsed >= 1.0:
        raise AssertionError(f"cached call took {elapsed:.4f}s; cache appears not to be serving repeats")

async def test_list_categories():
    print("\n--- Testing List Categories ---")
    result = await arxiv_list_categories()
    assert_ok(result, "list categories")
    if "cs.AI" not in result:
        raise AssertionError("list categories: expected 'cs.AI' in the taxonomy")
    print(result[:300] + "...")

async def main():
    try:
        await test_search()
        await test_advanced_search()
        await test_get_paper()
        test_partial_date_range_rejected()
        await test_rate_limiting_and_cache()
        await test_list_categories()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
