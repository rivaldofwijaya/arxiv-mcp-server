#!/usr/bin/env python3
import asyncio
import logging
from server import (
    arxiv_search, 
    arxiv_get_paper, 
    arxiv_list_categories,
    ArxivSearchInput,
    ArxivGetPaperInput,
    SortBy,
    SortOrder,
    ResponseFormat
)

# Setup basic logging to see the output
logging.basicConfig(level=logging.INFO)

async def test_search():
    print("\n--- Testing Basic Search ---")
    params = ArxivSearchInput(query="transformer attention", max_results=2)
    result = await arxiv_search(params)
    print(result[:500] + "...")

async def test_advanced_search():
    print("\n--- Testing Advanced Search (Boolean) ---")
    params = ArxivSearchInput(query="au:\"Yann LeCun\" AND ti:convolutional", max_results=1)
    result = await arxiv_search(params)
    print(result[:500] + "...")

async def test_get_paper():
    print("\n--- Testing Get Paper by ID ---")
    params = ArxivGetPaperInput(id_list=["1706.03762"]) # Attention is All You Need
    result = await arxiv_get_paper(params)
    print(result[:500] + "...")

async def test_rate_limiting_and_cache():
    print("\n--- Testing Rate Limiting and Cache ---")
    params = ArxivSearchInput(query="quantum computing", max_results=1)
    
    print("First call (should trigger API fetch and wait if needed):")
    await arxiv_search(params)
    
    print("\nSecond call (should be INSTANT due to cache):")
    start_time = asyncio.get_event_loop().time()
    await arxiv_search(params)
    end_time = asyncio.get_event_loop().time()
    print(f"Cache retrieval took: {end_time - start_time:.4f}s")

async def test_list_categories():
    print("\n--- Testing List Categories ---")
    result = await arxiv_list_categories()
    print(result[:300] + "...")

async def main():
    try:
        await test_search()
        await test_advanced_search()
        await test_get_paper()
        await test_rate_limiting_and_cache()
        await test_list_categories()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
