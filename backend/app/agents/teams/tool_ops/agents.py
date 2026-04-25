from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field

from app.skills.code_executor import execute_python_code


class ToolRequest(BaseModel):
    code: str = Field(min_length=1)
    language: str = "python"


class ToolResult(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


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

    request_model = ToolRequest(code=tool_request, language="python")
    return {
        "request": request_model.model_dump(),
        "team_iterations": state.get("team_iterations", 0) + 1,
    }


async def execute_tool_request(state: dict[str, Any]) -> dict[str, Any]:
    request_payload = ToolRequest.model_validate(
        state.get("request", {"code": "print('No tool request provided.')"})
    )
    executed = await execute_python_code(request_payload.code, timeout_seconds=8)
    result_model = ToolResult(
        stdout=str(executed.get("stdout", "")),
        stderr=str(executed.get("stderr", "")),
        exit_code=int(executed.get("exit_code", -1)),
    )
    return {"result": result_model.model_dump()}


async def craft_tool_response(state: dict[str, Any]) -> dict[str, Any]:
    result = ToolResult.model_validate(state.get("result", {}))
    stdout = result.stdout.strip() or "(empty)"
    stderr = result.stderr.strip() or "(empty)"
    exit_code = result.exit_code

    response = (
        "Tool Ops Result\n"
        f"Exit Code: {exit_code}\n"
        "Stdout:\n"
        f"{stdout}\n"
        "Stderr:\n"
        f"{stderr}"
    )
    return {"messages": [AIMessage(content=response)]}
