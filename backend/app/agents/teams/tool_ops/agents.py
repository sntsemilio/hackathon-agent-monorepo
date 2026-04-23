from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.skills.code_executor import execute_python_code


def _message_to_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(item) for item in content)
    return str(content)


def _latest_user_prompt(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            text = _message_to_text(message).strip()
            if text:
                return text
    if messages:
        return _message_to_text(messages[-1]).strip()
    return ""


def _extract_python_block(prompt: str) -> str | None:
    match = re.search(r"```(?:python)?\s*(.*?)```", prompt, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    extracted = match.group(1).strip()
    return extracted or None


async def prepare_tool_request(state: dict[str, Any]) -> dict[str, Any]:
    prompt = _latest_user_prompt(state.get("messages", []))
    tool_request = _extract_python_block(prompt)

    if tool_request is None:
        expression_match = re.search(
            r"(?:calculate|compute|evaluate)\s*[:\-]?\s*(.+)",
            prompt,
            re.IGNORECASE,
        )
        if expression_match:
            expression = expression_match.group(1).strip()
            tool_request = f"print({expression})"
        else:
            tool_request = "print('No executable Python code found in request.')"

    return {
        "tool_request": tool_request,
        "team_iterations": state.get("team_iterations", 0) + 1,
    }


async def execute_tool_request(state: dict[str, Any]) -> dict[str, Any]:
    tool_request = state.get("tool_request", "print('No tool request provided.')")
    tool_result = await execute_python_code(tool_request, timeout_seconds=8)
    return {"tool_result": tool_result}


async def craft_tool_response(state: dict[str, Any]) -> dict[str, Any]:
    result = state.get("tool_result", {})
    stdout = str(result.get("stdout", "")).strip() or "(empty)"
    stderr = str(result.get("stderr", "")).strip() or "(empty)"
    exit_code = result.get("exit_code", -1)

    response = (
        "Tool Ops Result\n"
        f"Exit Code: {exit_code}\n"
        "Stdout:\n"
        f"{stdout}\n"
        "Stderr:\n"
        f"{stderr}"
    )
    return {"messages": [AIMessage(content=response)]}
