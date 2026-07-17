from typing import Any


def extract_event_text(event: dict) -> str:
    """
    Extracts the most meaningful text from a LangGraph/ReAct event.

    Priority:
    1. AIMessage.content
    2. reasoning_content
    3. tool calls
    4. tool outputs
    """
    # print(event)
    try:
        # ---------------------------
        # MODEL EVENTS
        # ---------------------------
        if "model" in event:
            messages = event["model"].get("messages", [])

            outputs = []

            for msg in messages:

                # Final answer
                content = getattr(msg, "content", None)
                if content:
                    outputs.append(f"💬 {content}")

                # Reasoning
                reasoning = (
                    getattr(msg, "additional_kwargs", {})
                    .get("reasoning_content")
                )

                if reasoning and not content:
                    outputs.append(f"🧠 {reasoning}")

                # Tool calls
                tool_calls = getattr(msg, "tool_calls", [])

                for tool_call in tool_calls:
                    name = tool_call.get("name", "unknown_tool")
                    args = tool_call.get("args", {})

                    # outputs.append(
                    #     f"🔧 {name}({args})"
                    # )

                    outputs.append(
                        f"🔧 Using {name} tool."
                    )

            types = "model"
            tool_name = None
            content = "\n\n".join(outputs)

        # ---------------------------
        # TOOL EVENTS
        # ---------------------------
        if "tools" in event:
            messages = event["tools"].get("messages", [])

            outputs = []

            for msg in messages:

                tool_name = getattr(msg, "name", "tool")

                content = getattr(msg, "content", "")

                outputs.append(
                    f"✅ {tool_name}\n{content}"
                )

            types = "tool"
            tool_name = tool_name
            content = "\n\n".join(outputs)

        # return ""

    except Exception as e:

        types = "error"
        tool_name = None
        content = f"❌ Failed to parse event: {e}"

    return {
        "type": types,
        "tool_name": tool_name,
        "content": content
    }