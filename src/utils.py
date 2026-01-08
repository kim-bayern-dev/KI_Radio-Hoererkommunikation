import random
import re, html
from typing import List, Tuple, Optional
from functools import partial

from gradio import ChatMessage
from langchain.schema import AIMessage, HumanMessage, SystemMessage


class ContextMemory:
    """A class to manage the context memory for the chatbot."""

    def __init__(self):
        self.context_store = []

    def add_context(self, context: dict):
        """Add context to the memory."""
        self.context_store.append(context)

    def get_context(self) -> str:
        """Get the current context."""
        if not self.context_store:
            return "No context available."
        if len(self.context_store) == 1:
            return format_context(self.context_store[0])
        else:
            old_contexts = self.context_store[:-1]
            new_context = self.context_store[-1]
            formatted_old_contexts = [format_context(ctx) for ctx in old_contexts]
            formatted_new_context = format_context(new_context)
            return (
                "Vorherige Kontexte:\n"
                + "\n".join(formatted_old_contexts)
                + f"\n\nKontext:\n{formatted_new_context}"
            )

    def clear_context(self):
        """Clear the context memory."""
        self.context_store = []


def history_to_langchain_format(history: List) -> List:
    """
    Convert the conversation history to Langchain format.
    Args:
        history (list): The conversation history.
    Returns:
        list: The formatted conversation history.
    """
    history_langchain_format = []
    for msg in history:
        if msg["role"] == "user":
            history_langchain_format.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history_langchain_format.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "system":
            history_langchain_format.append(SystemMessage(content=msg["content"]))
    return history_langchain_format


# Regex pattern to match citations in the format [C1], [A2], etc.
CITE_PATTERN = re.compile(r"\[(C|A|S|T)(\d+)\]")


def _wrap_token(match, context_dict):
    "Wrap the matched token with a tooltip containing the context information source text."
    key = f"{match.group(1)}{match.group(2)}"
    full = html.escape(context_dict.get(key, "Source not found"))
    short = html.escape(full[:400]) + "..." if len(full) > 400 else html.escape(full)
    short = (
        short.replace("https://www.", "")
        .replace("[", "")
        .replace("]", "")
        .replace("#", "")
        .replace("(", "")
        .replace(")", "")
        .replace('"', "")
        .replace("&", "")
        .replace("_", " ")
        .replace("*", "")
        .replace("\n", " ")
    )
    return f'[{match.group(0)}(# "{short}")]'


def add_tooltips(msg: ChatMessage | str, context_dict: dict) -> ChatMessage | str:
    """
    Add tooltips to citations in the message content.

    Args:
        msg (ChatMessage | str): The message to process.
        context_dict (dict): A dictionary containing context information for citations.

    Returns:
        ChatMessage | str: The message with tooltips added to citations.
    """
    if isinstance(msg, ChatMessage):
        new_content = CITE_PATTERN.sub(
            partial(_wrap_token, context_dict=context_dict),
            msg.content.replace("[[", "[").replace("]]", "]"),
        )
        return ChatMessage(role=msg.role, content=new_content)
    elif isinstance(msg, str):
        return CITE_PATTERN.sub(partial(_wrap_token, context_dict=context_dict), msg)
    else:
        raise TypeError("Unsupported message type")


def handle_thinking(
    content: str, return_thoughts: bool = False
) -> Tuple[str, Optional[str]]:
    """
    Handle the <think> tags in the content.

    Args:
        content (str): The content to process.
        return_thoughts (bool): Whether to return the thoughts separately.

    Returns:
        Tuple[str, Optional[str]]: The processed content and thoughts if requested.
    """
    match = re.search(r"<think>(.*?)</think>", content, flags=re.DOTALL)
    if match:
        thought = match.group(1).strip()
    response = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    if return_thoughts:
        return (response, thought) if match else (response, None)
    return response


def random_subset(seq):
    """
    Return a list containing a random number (0-len(seq)) of
    elements chosen randomly from *seq* (without replacement).
    """
    k = random.randint(0, len(seq))
    return random.sample(seq, k)


def format_context(context_dict: dict) -> str:
    """
    Format the context dictionary into a string.

    Args:
        context_dict (dict): The context dictionary with ids as keys.

    Returns:
        str: A formatted string of the context.
    """
    context = []

    # aktionen
    if "A1" in context_dict:
        context.append("<aktionen>")
        for key, value in context_dict.items():
            if key.startswith("A"):
                context.append(f"[{key}] {value}")
        context.append("</aktionen>\n")
    # sendungen
    if "S1" in context_dict:
        context.append("<sendungen>")
        for key, value in context_dict.items():
            if key.startswith("S"):
                context.append(f"[{key}] {value}")
        context.append("</sendungen>\n")
    # teammitglieder
    if "T1" in context_dict:
        context.append("<teammitglieder>")
        for key, value in context_dict.items():
            if key.startswith("T"):
                context.append(f"[{key}] {value}")
        context.append("</teammitglieder>\n")
    # streams
    if "streams" in context_dict:
        context.append("<streams>")
        context.append(context_dict["streams"])
        context.append("</streams>\n")
    # live-programm
    if "C1" in context_dict:
        context.append("<live-programm>")
        for key, value in context_dict.items():
            if key.startswith("C"):
                context.append(f"[{key}] {value}")
        context.append("</live-programm>\n")

    return "\n".join(context)
