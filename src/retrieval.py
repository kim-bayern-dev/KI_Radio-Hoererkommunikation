import json
from enum import Enum
from typing import List, Dict, Tuple

from langchain.schema import HumanMessage
from langchain_core.runnables import RunnablePassthrough

from utils import handle_thinking, random_subset
from db.query import query_website_db
from llm.prompt_management import PromptStore
from config_utils import AppConfig


def get_linksammlung():
    """Get the linksammlung from the local file."""
    with open("src/linksammlung.json", "r", encoding="utf-8") as f:
        linksammlung = f.read()
    return linksammlung


def get_streams(streams_path: str) -> List[Dict]:
    """
    Get the streams from the local file.
    """
    with open(streams_path, "r", encoding="utf-8") as f:
        streams = json.load(f)
    return streams


class Source(Enum):
    """
    Enum for the available sources for retrieval.
    """

    ACTIONS = "Aktionen"
    SHOWS = "Sendungen"
    TEAM_MEMBERS = "Teammitglieder"
    STREAMS = "Streams"
    LINKS = "Linksammlung"


class RetrievalLLM:
    def __init__(
        self,
        model,
        prompt_store: PromptStore,
        config: AppConfig,
    ):
        """
        Initialize the RetrievalLLM with a model, prompt store, and Langfuse handler.

        Args:
            model: The LLM model to use for retrieval.
            prompt_store (PromptStore): The prompt store to retrieve prompts.
            config (AppConfig): The application configuration.
        """
        self.model = model
        self.prompt_store = prompt_store
        self.config = config
        sources = config.data.sources

        # Set the available additional sources for retrieval
        if not sources:
            print("No sources provided, using no additional sources.")
            self.sources = []
        try:
            self.sources = [Source(s) for s in sources]
        except ValueError as e:
            raise ValueError(
                f"Invalid source provided. Available sources are: {[s.value for s in Source]}"
            ) from e

    def get_context(
        self,
        query: str,
        date_today: str,
        last_chunk_timestamp: str,
        retriever=None,
    ) -> dict:
        context_dict = dict()

        # Check if the model needs additional context
        required_sources = _select_sources(
            query, self.sources, self.model, self.prompt_store
        )
        if not required_sources:
            print("No additional context required.")

        # Get the required additional information based on the selected sources
        required_additional_info = _get_required_additional_info(
            query,
            required_sources,
            self.config.embeddings.model,
            self.config.embeddings.base_url,
            self.config.data.db_uri,
            self.config.data.streams_path,
        )
        if not required_additional_info:
            print("No additional information available.")
        context_dict.update(required_additional_info)

        # Get the semantic query for the retrieval from the live program
        semantic_query, start_time, end_time = _get_semantic_query(
            query,
            self.model,
            prompt_store=self.prompt_store,
            date_today=date_today,
            last_chunk_timestamp=last_chunk_timestamp,
        )

        # Retrieve the context from the live program database based on the semantic query
        live_program_context = _retrieve_from_live_program(
            semantic_query,
            start_time,
            end_time,
            retriever,
        )
        if not live_program_context:
            print("No context retrieved from the live program.")
        context_dict.update(live_program_context)

        return context_dict


def _select_sources(
    query: str,
    available_sources: List[Source],
    model,
    prompt_store: PromptStore,
) -> List[str]:
    """
    Ask the model which additional sources are required for the given query.

    Args:
        query (str): The user query for which additional context is needed.
        available_sources (List[Source]): The list of available sources for retrieval.
        model: The LLM model to use for source selection.
        prompt_store (PromptStore): The prompt store to retrieve prompts.

    Returns:
        List[str]: A list of required additional sources based on the model's response.
    """
    examples = [
        "[" + ",".join(random_subset([s.value for s in available_sources])) + "]"
        for _ in range(5)
    ] + ["[]"]

    prompt = prompt_store.get_prompt("source-selection-prompt")
    response = model.invoke(
        [
            HumanMessage(
                content=prompt.compile(query=query, examples="\n".join(examples))
            )
        ]
    )
    try:
        required_additional_info = [
            info.value for info in available_sources if info.value in response.content
        ]
        print(f"Required additional info: {required_additional_info}")
    except:
        print("Error parsing the additional context response.")
        required_additional_info = []
    return required_additional_info


def _get_required_additional_info(
    query: str,
    required_additional_info: List[str],
    embedding_model: str,
    embedding_base_url: str,
    db_uri: str,
    streams_path: str,
) -> Dict:
    """
    Retrieve the required additional information based on the selected sources.

    Args:
        query (str): The user query for which additional context is needed.
        required_additional_info (List[str]): The list of required additional information based on the selected sources.
        embedding_model (str): The embedding model to use for querying the database.
        embedding_base_url (str): The base URL for the embedding model service.
        db_uri (str): The URI of the LanceDB database.
        streams_path (str): The path to the streams JSON file.

    Returns:
        dict: A dictionary containing the required additional information.
    """
    context_dict = dict()
    for req in required_additional_info:
        if req == "Aktionen":
            actions = query_website_db(
                query=query,
                type="aktionen",
                db_uri=db_uri,
                embedding_model=embedding_model,
                embedding_base_url=embedding_base_url,
            )
            for idx, action in enumerate(actions):
                context_dict[f"A{idx + 1}"] = (
                    f"{action['title']} (Seite vom {action['date']}, URL: {action['url']}):\n{action['summary']}\n{action['full_text']}"
                )
        elif req == "Sendungen":
            shows = query_website_db(
                query=query,
                type="sendungen",
                db_uri=db_uri,
                embedding_model=embedding_model,
                embedding_base_url=embedding_base_url,
            )
            for idx, item in enumerate(shows):
                context_dict[f"S{idx + 1}"] = (
                    f"{item['title']} moderiert von {item['team_members']} immer {item['schedule']} (URL:{item['url']}):\n{item['summary']}\n{item['full_text']}"
                )
        elif req == "Teammitglieder":
            team = query_website_db(
                query=query,
                type="team",
                top_n=2,
                db_uri=db_uri,
                embedding_model=embedding_model,
                embedding_base_url=embedding_base_url,
            )
            for idx, item in enumerate(team):
                context_dict[f"T{idx + 1}"] = (
                    f"{item['title']}: {item['summary']}\n{item['full_text']}"
                )
        elif req == "Streams":
            streams = get_streams(streams_path=streams_path)
            context_dict["streams"] = "\n".join(
                [
                    f"{item['name']} (URL: {item['url']}): {item['description']}"
                    for item in streams
                ]
            )
        else:
            print(f"Unknown context type: {req}")
    return context_dict


def _get_semantic_query(
    query: str,
    model,
    prompt_store: PromptStore = None,
    date_today: str = None,
    last_chunk_timestamp: str = None,
) -> Tuple[str, str, str]:
    """
    Get the semantic query for the retrieval from the live program database.

    Args:
        query (str): The user query for which the semantic query is needed.
        model: The LLM model to use for generating the semantic query.
        prompt_store (PromptStore): The prompt store to retrieve prompts.
        date_today (str): The current date in string format.
        last_chunk_timestamp (str): The timestamp of the last chunk.

    Returns:
        tuple: A tuple containing the semantic query, start time, and end time.
    """
    llm_chain = RunnablePassthrough() | model
    # get the prompt
    prompt = prompt_store.get_prompt("retrieval-prompt")
    response = llm_chain.invoke(
        [
            HumanMessage(
                content=prompt.compile(
                    query=query,
                    date=date_today,
                    last_chunk_timestamp=last_chunk_timestamp,
                )
            ),
        ],
        config={"temperature": 0.0},
    )
    model_response = handle_thinking(response.content, return_thoughts=False)
    # Check if the response is valid
    try:
        semantic_query, timerange = model_response.split("#")
        starttime, endtime = timerange.split(",")
    except:
        print("Error parsing the response.")
        semantic_query = model_response
        starttime, endtime = "", ""
    return semantic_query.strip(), starttime.strip(), endtime.strip()


def _retrieve_from_live_program(
    semantic_query: str,
    starttime: str,
    endtime: str,
    retriever,
) -> Dict:
    """
    Retrieve the context from the live program database based on the semantic query.

    Args:
        semantic_query (str): The semantic query for the retrieval.
        starttime (str): The start time for the retrieval.
        endtime (str): The end time for the retrieval.
        retriever: The retriever to use for querying the live program database.

    Returns:
        dict: A dictionary containing the retrieved context from the live program.
    """
    print("Querying the live radio program...")
    # Run the retriever with the semantic query
    result = retriever.invoke(
        input={
            "semantic_query": semantic_query,
            "starttime": starttime,
            "endtime": endtime,
            "num_results": 7,
        },
    )
    context_dict = dict()
    for idx, item in enumerate(result):
        context_dict[f"C{idx + 1}"] = f"{item.get('starttime')}: {item['text']}"
    return context_dict
