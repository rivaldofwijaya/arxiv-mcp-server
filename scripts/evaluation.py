"""MCP Server Evaluation Harness

This script evaluates MCP servers by running test questions against them using OpenRouter (OpenAI-compatible API).
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from openai import OpenAI

from connections import create_connection

# Bounds for the agent loop. Without these a model that keeps emitting tool calls
# (or retries a persistently failing tool) can hang the run, burn OpenRouter
# credit, and hammer the arXiv API indefinitely.
DEFAULT_MAX_TOOL_ROUNDS = 10
DEFAULT_TASK_TIMEOUT_S = 300.0


class TaskLimitExceeded(RuntimeError):
    """Raised when a task exceeds its tool-round or wall-clock budget."""


EVALUATION_PROMPT = """You are an AI assistant with access to tools.

When given a task, you MUST:
1. Use the available tools to complete the task
2. Provide summary of each step in your approach, wrapped in <summary> tags
3. Provide feedback on the tools provided, wrapped in <feedback> tags
4. Provide your final response, wrapped in <response> tags

Summary Requirements:
- In your <summary> tags, you must explain:
  - The steps you took to complete the task
  - Which tools you used, in what order, and why
  - The inputs you provided to each tool
  - The outputs you received from each tool
  - A summary for how you arrived at the response

Feedback Requirements:
- In your <feedback> tags, provide constructive feedback on the tools:
  - Comment on tool names: Are they clear and descriptive?
  - Comment on input parameters: Are they well-documented? Are required vs optional parameters clear?
  - Comment on descriptions: Do they accurately describe what the tool does?
  - Comment on any errors encountered during tool usage: Did the tool fail to execute? Did the tool return too many tokens?
  - Identify specific areas for improvement and explain WHY they would help
  - Be specific and actionable in your suggestions

Response Requirements:
- Your response should be concise and directly address what was asked
- Always wrap your final response in <response> tags
- If you cannot solve the task return <response>NOT_FOUND</response>
- For numeric responses, provide just the number
- For IDs, provide just the ID
- For names or text, provide the exact text requested
- Your response should go last"""


def parse_evaluation_file(file_path: Path) -> list[dict[str, Any]]:
    """Parse XML evaluation file with qa_pair elements."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        evaluations = []

        for qa_pair in root.findall(".//qa_pair"):
            question_elem = qa_pair.find("question")
            answer_elem = qa_pair.find("answer")

            if question_elem is not None and answer_elem is not None:
                evaluations.append({
                    "question": (question_elem.text or "").strip(),
                    "answer": (answer_elem.text or "").strip(),
                })

        return evaluations
    except Exception as e:
        print(f"Error parsing evaluation file {file_path}: {e}")
        return []


def extract_xml_content(text: str, tag: str) -> str | None:
    """Extract content from XML tags."""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[-1].strip() if matches else None


async def agent_loop(
    client: OpenAI,
    model: str,
    question: str,
    tools: list[dict[str, Any]],
    connection: Any,
    max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
    timeout_s: float = DEFAULT_TASK_TIMEOUT_S,
) -> tuple[str, dict[str, Any]]:
    """Run the agent loop with MCP tools via OpenRouter.

    The loop is bounded by both `max_tool_rounds` and `timeout_s`; exceeding
    either raises TaskLimitExceeded so the caller can record the task as failed.
    """
    deadline = time.time() + timeout_s
    messages = [{"role": "user", "content": question}]
    
    # Convert MCP tool schema to OpenAI tool schema
    openai_tools = []
    for tool in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        })

    # Initial call
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=model,
        messages=[
            {"role": "system", "content": EVALUATION_PROMPT},
            *messages
        ],
        tools=openai_tools,
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message
    messages.append(assistant_message)
    
    tool_metrics = {}
    tool_rounds = 0

    while assistant_message.tool_calls:
        tool_rounds += 1
        if tool_rounds > max_tool_rounds:
            raise TaskLimitExceeded(
                f"Exceeded max tool rounds ({max_tool_rounds}) without a final answer"
            )
        if time.time() > deadline:
            raise TaskLimitExceeded(
                f"Exceeded task timeout ({timeout_s:.0f}s) without a final answer"
            )

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_input = json.loads(tool_call.function.arguments)

            print(f"🛠️ Calling tool: {tool_name} with args: {tool_input}")
            tool_start_ts = time.time()
            try:
                # call_tool returns a list of content blocks in MCP, we need to extract the text
                tool_result_blocks = await connection.call_tool(tool_name, tool_input)
                tool_response = ""
                for block in tool_result_blocks:
                    if hasattr(block, 'text'):
                        tool_response += block.text
                    elif isinstance(block, dict) and 'text' in block:
                        tool_response += block['text']
                    else:
                        tool_response += str(block)
                
            except Exception as e:
                tool_response = f"Error executing tool {tool_name}: {str(e)}\n"
                tool_response += traceback.format_exc()
            
            tool_duration = time.time() - tool_start_ts

            if tool_name not in tool_metrics:
                tool_metrics[tool_name] = {"count": 0, "durations": []}
            tool_metrics[tool_name]["count"] += 1
            tool_metrics[tool_name]["durations"].append(tool_duration)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": tool_response,
            })

        # Get next response from model
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=[
                {"role": "system", "content": EVALUATION_PROMPT},
                *messages
            ],
            tools=openai_tools
        )
        assistant_message = response.choices[0].message
        messages.append(assistant_message)

    return assistant_message.content or "", tool_metrics


async def evaluate_single_task(
    client: OpenAI,
    model: str,
    qa_pair: dict[str, Any],
    tools: list[dict[str, Any]],
    connection: Any,
    task_index: int,
    max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
    timeout_s: float = DEFAULT_TASK_TIMEOUT_S,
) -> dict[str, Any]:
    """Evaluate a single QA pair with the given tools."""
    start_time = time.time()

    print(f"\n--- Task {task_index + 1}: {qa_pair['question']} ---")
    try:
        response, tool_metrics = await agent_loop(
            client, model, qa_pair["question"], tools, connection,
            max_tool_rounds=max_tool_rounds,
            timeout_s=timeout_s,
        )
        
        response_value = extract_xml_content(response, "response")
        summary = extract_xml_content(response, "summary")
        feedback = extract_xml_content(response, "feedback")

        duration_seconds = time.time() - start_time

        return {
            "question": qa_pair["question"],
            "expected": qa_pair["answer"],
            "actual": response_value,
            "score": int(response_value.lower() == qa_pair["answer"].lower()) if response_value else 0,
            "total_duration": duration_seconds,
            "tool_calls": tool_metrics,
            "num_tool_calls": sum(len(metrics["durations"]) for metrics in tool_metrics.values()),
            "summary": summary,
            "feedback": feedback,
        }
    except TaskLimitExceeded as e:
        print(f"⏱️ Task {task_index + 1} aborted: {e}")
        return {
            "question": qa_pair["question"],
            "expected": qa_pair["answer"],
            "actual": f"ABORTED: {str(e)}",
            "score": 0,
            "total_duration": time.time() - start_time,
            "tool_calls": {},
            "num_tool_calls": 0,
            "summary": "N/A",
            "feedback": f"Task aborted by budget guard: {str(e)}",
        }
    except Exception as e:
        print(f"❌ Error evaluating task {task_index + 1}: {e}")
        traceback.print_exc()
        return {
            "question": qa_pair["question"],
            "expected": qa_pair["answer"],
            "actual": f"ERROR: {str(e)}",
            "score": 0,
            "total_duration": time.time() - start_time,
            "tool_calls": {},
            "num_tool_calls": 0,
            "summary": "N/A",
            "feedback": f"Critical Error: {str(e)}",
        }


REPORT_HEADER = """
# Evaluation Report

## Summary

- **Accuracy**: {correct}/{total} ({accuracy:.1f}%)
- **Average Task Duration**: {average_duration_s:.2f}s
- **Average Tool Calls per Task**: {average_tool_calls:.2f}
- **Total Tool Calls**: {total_tool_calls}

---
"""

TASK_TEMPLATE = """
### Task {task_num}

**Question**: {question}
**Ground Truth Answer**: `{expected_answer}`
**Actual Answer**: `{actual_answer}`
**Correct**: {correct_indicator}
**Duration**: {total_duration:.2f}s
**Tool Calls**: {tool_calls}

**Summary**
{summary}

**Feedback**
{feedback}

---
"""


async def run_evaluation(
    eval_path: Path,
    connection: Any,
    api_key: str,
    model: str,
    max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
    timeout_s: float = DEFAULT_TASK_TIMEOUT_S,
) -> str:
    """Run evaluation with MCP server tools."""
    print(f"🚀 Starting Evaluation with model: {model}")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "X-Title": "arxiv-mcpserver Evaluation",
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity"
        }
    )

    tools = await connection.list_tools()
    print(f"📋 Loaded {len(tools)} tools from MCP server")

    qa_pairs = parse_evaluation_file(eval_path)
    print(f"📋 Loaded {len(qa_pairs)} evaluation tasks")

    results = []
    for i, qa_pair in enumerate(qa_pairs):
        print(f"Processing task {i + 1}/{len(qa_pairs)}")
        result = await evaluate_single_task(
            client, model, qa_pair, tools, connection, i,
            max_tool_rounds=max_tool_rounds,
            timeout_s=timeout_s,
        )
        results.append(result)

    correct = sum(r["score"] for r in results)
    accuracy = (correct / len(results)) * 100 if results else 0
    average_duration_s = sum(r["total_duration"] for r in results) / len(results) if results else 0
    average_tool_calls = sum(r["num_tool_calls"] for r in results) / len(results) if results else 0
    total_tool_calls = sum(r["num_tool_calls"] for r in results)

    report = REPORT_HEADER.format(
        correct=correct,
        total=len(results),
        accuracy=accuracy,
        average_duration_s=average_duration_s,
        average_tool_calls=average_tool_calls,
        total_tool_calls=total_tool_calls,
    )

    report += "".join([
        TASK_TEMPLATE.format(
            task_num=i + 1,
            question=qa_pair["question"],
            expected_answer=qa_pair["answer"],
            actual_answer=result["actual"] or "N/A",
            correct_indicator="✅" if result["score"] else "❌",
            total_duration=result["total_duration"],
            tool_calls=json.dumps(result["tool_calls"], indent=2),
            summary=result["summary"] or "N/A",
            feedback=result["feedback"] or "N/A",
        )
        for i, (qa_pair, result) in enumerate(zip(qa_pairs, results))
    ])

    return report


async def main():
    parser = argparse.ArgumentParser(
        description="Evaluate MCP servers using test questions via OpenRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("eval_file", type=Path, help="Path to evaluation XML file")
    parser.add_argument("-t", "--transport", choices=["stdio", "sse", "http"], default="stdio", help="Transport type (default: stdio)")
    parser.add_argument("-m", "--model", required=True, help="OpenRouter model ID (e.g., minimax/minimax-01)")
    parser.add_argument("-k", "--key", help="OpenRouter API Key (can also use OPENROUTER_API_KEY env var)")

    stdio_group = parser.add_argument_group("stdio options")
    stdio_group.add_argument("-c", "--command", help="Command to run MCP server (stdio only)")
    stdio_group.add_argument("-a", "--args", nargs="+", help="Arguments for the command (stdio only)")
    stdio_group.add_argument("-e", "--env", nargs="+", help="Environment variables in KEY=VALUE format (stdio only)")

    remote_group = parser.add_argument_group("sse/http options")
    remote_group.add_argument("-u", "--url", help="MCP server URL (required for sse and http transports)")
    remote_group.add_argument("-H", "--header", nargs="+", help="HTTP headers in KEY=VALUE format (sse and http only)")

    parser.add_argument("-o", "--output", type=Path, help="Output file for evaluation report (default: stdout)")
    parser.add_argument(
        "--max-tool-rounds", type=int, default=DEFAULT_MAX_TOOL_ROUNDS,
        help=f"Max tool-call rounds per task before aborting it (default: {DEFAULT_MAX_TOOL_ROUNDS})",
    )
    parser.add_argument(
        "--task-timeout", type=float, default=DEFAULT_TASK_TIMEOUT_S,
        help=f"Wall-clock budget in seconds per task (default: {DEFAULT_TASK_TIMEOUT_S:.0f})",
    )

    args = parser.parse_args()

    api_key = args.key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OpenRouter API Key must be provided via -k or OPENROUTER_API_KEY environment variable")
        sys.exit(1)

    if not args.eval_file.exists():
        print(f"Error: Evaluation file not found: {args.eval_file}")
        sys.exit(1)

    if args.max_tool_rounds < 1:
        print("Error: --max-tool-rounds must be at least 1")
        sys.exit(1)

    if args.task_timeout <= 0:
        print("Error: --task-timeout must be greater than 0")
        sys.exit(1)

    try:
        connection = create_connection(
            transport=args.transport,
            command=args.command,
            args=args.args,
            env=parse_env_vars(args.env) if args.env else None,
            url=args.url,
            headers=parse_env_vars(args.header) if args.header else None,
        )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"🔗 Connecting to MCP server via {args.transport}...")

    async with connection:
        print("✅ Connected successfully")
        report = await run_evaluation(
            args.eval_file, connection, api_key, args.model,
            max_tool_rounds=args.max_tool_rounds,
            timeout_s=args.task_timeout,
        )

        if args.output:
            args.output.write_text(report)
            print(f"\n✅ Report saved to {args.output}")
        else:
            print("\n" + report)


def parse_env_vars(env_list: list[str]) -> dict[str, str]:
    """Parse 'KEY=VALUE' strings into a dictionary (used for env vars and HTTP headers)."""
    env = {}
    if not env_list:
        return env

    for env_var in env_list:
        if "=" in env_var:
            key, value = env_var.split("=", 1)
            env[key.strip()] = value.strip()
    return env


if __name__ == "__main__":
    asyncio.run(main())
