from langchain_core.runnables import RunnablePassthrough
from langchain.schema import HumanMessage, SystemMessage
from llm.prompt_management import PromptStore
from utils import handle_thinking


class FilterLLM:
    def __init__(self, model, prompt_store: PromptStore):
        """
        Initialize the FilterLLM with a model and prompt store.

        Args:
            model: The LLM model to use for filtering.
            prompt_store (PromptStore): The prompt store to retrieve prompts.
        """
        self.model = model
        self.prompt_store = prompt_store

    def filter(self, message: str) -> bool:
        """
        Call the filter_message function to filter the message.

        Args:
            message (str): The message to filter.

        Returns:
            bool: True if the message is allowed, False if it should be blocked.
        """
        return _filter_message(
            message,
            self.model,
            self.prompt_store,
        )


def _filter_message(
    message: str,
    model,
    prompt_store: PromptStore,
) -> bool:
    """
    Filter the message to block any unwanted conversation attempts.

    Args:
        message (str): The message to filter.
        model: The LLM model to use for filtering.
        prompt_store: The prompt store to retrieve prompts.

    Returns:
        bool: True if the message is allowed, False if it should be blocked.
    """
    # Create the prompt for the model
    prompt = prompt_store.get_prompt("filter-prompt")
    system_prompt = prompt_store.get_prompt("filter-prompt-system")
    history_langchain_format = [
        SystemMessage(content=system_prompt.compile()),
        HumanMessage(content=prompt.compile(message=message)),
    ]

    llm_chain = RunnablePassthrough() | model
    response = llm_chain.invoke(
        history_langchain_format,
        config={"temperature": 0},
    )
    # Handle the response from the model
    model_response = handle_thinking(response.content, return_thoughts=False)

    # Process the response to determine if the message is allowed
    try:
        if model_response == "ja":
            return True
        elif model_response == "nein":
            return False
        else:
            print(f"Unexpected response: {model_response}")
            return False
    except Exception as e:
        print(f"Error processing response: {e}")
        return False
