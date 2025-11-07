#!/usr/bin/env python3

"""Smoke tests for the Draft Finnish MCP server."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

# Ensure the module is importable when the test is run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helsinki_transport import draft_finnish


async def test_missing_endpoint() -> None:
    """Verify that a helpful error is returned when the endpoint is unset."""

    os.environ.pop("VLLM_ENDPOINT", None)

    result = await draft_finnish("Hei maailma!")
    print("Missing endpoint response:\n", result)


async def test_successful_completion() -> None:
    """Verify that the tool forwards prompts and returns the completion text."""

    os.environ["VLLM_ENDPOINT"] = "http://mock.local/v1/chat/completions"
    os.environ["VLLM_MODEL"] = "mock-model"

    mock_response = {"choices": [{"message": {"content": " Hei! Miten voin auttaa? "}}]}

    with patch("helsinki_transport._post_to_vllm", new=AsyncMock(return_value=mock_response)) as mocked_post:
        result = await draft_finnish("Voitko kirjoittaa lyhyen tervehdyksen?")

    print("Mocked completion:\n", result)
    mocked_post.assert_awaited_once()


async def main() -> int:
    """Run smoke tests sequentially."""

    print("Draft Finnish MCP Server Test Suite")
    print("=" * 50)

    try:
        await test_missing_endpoint()
        await test_successful_completion()
        print("✅ All smoke tests completed successfully!")
    except Exception as exc:  # pragma: no cover - diagnostic output
        print(f"❌ Test failed with error: {exc}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    EXIT_CODE = asyncio.run(main())
    sys.exit(EXIT_CODE)
