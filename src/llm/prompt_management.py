import re

from llm.prompts import (
    SOURCE_SELECTION_PROMPT,
    FILTER_PROMPT_TEMPLATE,
    FILTER_PROMPT_SYSTEM_TEMPLATE,
    GENERATION_PROMPT_SYSTEM_TEMPLATE,
    GENERATION_PROMPT_TEMPLATE,
    CRITIQUE_PROMPT_SYSTEM_TEMPLATE,
    CRITIQUE_PROMPT_TEMPLATE,
    RETRIEVAL_PROMPT_TEMPLATE,
    CONTEXT_PROMPT_TEMPLATE,
)
from config_utils import AppConfig


class SafeDict(dict):
    """Return the placeholder unchanged when a key is missing."""

    def __missing__(self, key):
        return "{" + key + "}"


_single_field = re.compile(r"(?<!{){([^{}]+)}(?!})")


def partial_format(text: str, **vals):
    def repl(match):
        name = match.group(1)
        return str(vals[name]) if name in vals else match.group(0)

    return _single_field.sub(repl, text)


class LocalPromptTemplate:
    """A class to retrieve prompts locally."""

    def __init__(self, prompt: str, config: AppConfig):
        self.config = config
        self._prompt = pre_format_prompt(prompt, config)
        self.is_fallback = True

    def compile(self, **kwargs) -> str:
        """Compile the prompt with the given arguments."""
        return self._prompt.format(**kwargs)


def pre_format_prompt(prompt: str, config: AppConfig) -> str:
    """Pre-format the prompt with configuration values."""
    return partial_format(
        prompt,
        STATION_NAME=config.constants.station_name,
        STATION_URL=config.constants.station_url,
        CONTACT_LINK=config.constants.contact_link,
        SERVICE_EMAIL=config.constants.service_email,
        LINKS="\n".join(config.constants.links),
    )


class PromptStore:
    """A class to retrieve prompts."""

    def __init__(self, config: AppConfig):
        self.config = config
        self._local_prompts = {
            "generation-prompt": LocalPromptTemplate(
                GENERATION_PROMPT_TEMPLATE, config
            ),
            "generation-prompt-system": LocalPromptTemplate(
                GENERATION_PROMPT_SYSTEM_TEMPLATE, config
            ),
            "critique-prompt": LocalPromptTemplate(CRITIQUE_PROMPT_TEMPLATE, config),
            "critique-prompt-system": LocalPromptTemplate(
                CRITIQUE_PROMPT_SYSTEM_TEMPLATE, config
            ),
            "retrieval-prompt": LocalPromptTemplate(RETRIEVAL_PROMPT_TEMPLATE, config),
            "context-prompt": LocalPromptTemplate(CONTEXT_PROMPT_TEMPLATE, config),
            "filter-prompt": LocalPromptTemplate(FILTER_PROMPT_TEMPLATE, config),
            "filter-prompt-system": LocalPromptTemplate(
                FILTER_PROMPT_SYSTEM_TEMPLATE, config
            ),
            "source-selection-prompt": LocalPromptTemplate(
                SOURCE_SELECTION_PROMPT, config
            ),
        }

    def get_prompt(self, prompt_name: str) -> LocalPromptTemplate:
        """Retrieve a prompt by name."""
        # Fallback to local prompt
        if prompt_name not in self._local_prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found in local prompts.")
        return self._local_prompts[prompt_name]
