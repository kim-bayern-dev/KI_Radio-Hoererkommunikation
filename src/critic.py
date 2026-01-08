import json

from langchain_core.runnables import RunnablePassthrough
from langchain.schema import HumanMessage, SystemMessage

from utils import handle_thinking
from llm.prompt_management import PromptStore


class Feedback:
    """A class to represent the feedback from the LLM critique."""

    def __init__(self, raw_feedback: str):
        """
        Initialize the Feedback object with raw feedback.

        Args:
            raw_feedback (str): The raw feedback string from the LLM.
        """
        self.raw_feedback = raw_feedback

        self.process_feedback()

    def process_feedback(self):
        try:
            self.feedback_json = json.loads(self.raw_feedback)
        except json.JSONDecodeError:
            print("Error decoding JSON from feedback")

    @property
    def accepted(self) -> bool:
        """
        Check if the feedback indicates that the answer is acceptable.

        Returns:
            bool: True if the answer is acceptable, False otherwise.
        """
        if not hasattr(self, "feedback_json"):
            return False
        return self.feedback_json.get("accepted", False)

    @property
    def message(self) -> str:
        """
        Get the feedback message from the LLM.

        Returns:
            str: The feedback message.
        """
        if not hasattr(self, "feedback_json"):
            return "Failed to process feedback."
        return self.feedback_json.get("feedback", "No feedback provided.")


class CriticLLM:
    def __init__(self, model, prompt_store: PromptStore):
        """
        Initialize the CriticLLM with a model and prompt store.

        Args:
            model: The LLM model to use for critique.
            prompt_store (PromptStore): The prompt store to retrieve prompts.
        """
        self.model = model
        self.prompt_store = prompt_store

    def give_feedback(self, query: str, answer: str, context: str) -> Feedback:
        """
        Call the critique function to give feedback on the answer.

        Args:
            query (str): The user query.
            answer (str): The model's answer.
            context (str): The context used to generate the answer.

        Returns:
            Feedback: An instance of the Feedback class containing the raw and parsed feedback.
        """
        raw_feedback = _give_feedback(
            query,
            answer,
            context,
            self.model,
            self.prompt_store,
        )
        return Feedback(raw_feedback)


def _give_feedback(
    query: str,
    answer: str,
    context: str,
    model,
    prompt_store: PromptStore,
) -> str:
    """Implementation of a LLM critique function.
    Args:
        query (str): The user query.
        answer (str): The model's answer.
        context (str): The context used to generate the answer.
        model: The LLM model to use for critique.
        prompt_store: The prompt store to retrieve prompts.

    Returns:
        str: The raw feedback from the LLM, which is expected to be in JSON format.
    """
    # Create the prompt for the model
    prompt = prompt_store.get_prompt("critique-prompt")
    system_prompt = prompt_store.get_prompt("critique-prompt-system")
    history_langchain_format = [
        SystemMessage(content=system_prompt.compile()),
        HumanMessage(
            content=prompt.compile(query=query, answer=answer, context=context)
        ),
    ]

    llm_chain = RunnablePassthrough() | model
    response = llm_chain.invoke(
        history_langchain_format,
        config={"temperature": 0},
    )
    # remove everything between <thinking> and </thinking> with a regular expression
    model_response = handle_thinking(response.content, return_thoughts=False)
    return model_response.strip("```json").strip("```").strip()
