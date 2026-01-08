"""Main entry point to start the chatbot application."""

import time
import random, click
import regex as re
from typing import Dict
from pathlib import Path
from functools import partial

import gradio as gr
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from theme import theme
from db.query import get_retriever
from llm.models import get_model
from llm.prompt_management import PromptStore
from retrieval import RetrievalLLM
from critic import CriticLLM
from utils import (
    history_to_langchain_format,
    ContextMemory,
    add_tooltips,
    format_context,
)
from filtering import FilterLLM
from constants import STANDARD_RESPONSES
from config_utils import AppConfig


# Constants for the simulated live radio environment
DATE_TODAY = "2025-06-10"
LAST_CHUNK_TIMESTAMP = "2025-06-10 10:00"

retriever, model, prompt_store = None, None, None

# Initialize the context memory
context_memory = ContextMemory()


ASSETS = Path(__file__).parent.parent / "assets"
gr.set_static_paths([ASSETS])


def initialize(config: AppConfig):
    # Initialize the retriever
    global retriever
    retriever = get_retriever(config=config, table_name="live")

    # Initialize the model
    # Note: we use the same model for all LLM tasks in this application
    global model
    model = get_model(
        name=config.model.name,
        temperature=config.model.temperature,
        base_url=config.model.base_url,
    )

    # Initialize the prompt store
    global prompt_store
    prompt_store = PromptStore(config=config)


def _stream_reply(history_langchain_format, session_id: str = None, model=None):
    """Stream the reply from the model.

    Args:
        history_langchain_format (list): The conversation history in Langchain format.
        session_id (str): The session ID for tracking.
        model: The LLM model to use for generating the answer.

    Yields:
        str: The generated response from the model, with certain tags and comments removed.
    """
    llm_chain = RunnablePassthrough() | model
    stream = llm_chain.stream(history_langchain_format)
    full = next(stream)
    for chunk in stream:
        full += chunk
        # remove everything between <think> and </think> or ending with a regular expression
        response = re.sub(r"<think>.*?(?:</think>|$)", "", full.text(), flags=re.DOTALL)
        # remove all lines starting with #
        response = re.sub(r"^#.*\n", "", response, flags=re.MULTILINE)
        yield response


def generate_answer(
    history,
    message,
    context: str = "Keine weiteren Informationen.",
    model=None,
    previous_message="",
    feedback_message="",
):
    """Generate an answer using the model.

    Args:
        history (list): The conversation history.
        message (str): The user message.
        context (list): The context retrieved from the database.
        model: The LLM model to use for generating the answer.
        previous_message (str): The previous message from the assistant.
        feedback_message (str): The feedback message from the critic.

    Yields:
        str: The generated answer.
    """
    # Create the prompt for the model
    history_langchain_format = history_to_langchain_format(history)

    # Add the system message to the history
    system_prompt = prompt_store.get_prompt("generation-prompt-system")
    history_langchain_format.insert(0, SystemMessage(content=system_prompt.compile()))
    # Add the feedback message to the history if it exists
    if feedback_message:
        history_langchain_format.append(
            AIMessage(
                content=f"Der Senderbeauftragte hat die vorherige Antwort abgelehnt:\n<vorherige antwort>{previous_message}</vorherige antwort>\n\nBegründung:\n<begruendung>{feedback_message}</begruendung>\n\nBitte nimm dir das Feedback zu Herzen und versuche es erneut."
            )
        )

    # Add the user message and context to the history
    prompt = prompt_store.get_prompt("generation-prompt")
    context_prompt = prompt_store.get_prompt("context-prompt")
    history_langchain_format.extend(
        [
            AIMessage(content=context_prompt.compile(context=context)),
            HumanMessage(content=prompt.compile(message=message)),
        ]
    )
    # Invoke the model with the updated history and stream the response
    for full in _stream_reply(history_langchain_format, model=model):
        yield full


def process_message(message, history, config: AppConfig):
    """
    Process the user message and return the model's response.

    Args:
        message (str): The user message.
        history (list): The conversation history.
        config (AppConfig): The application configuration.

    Returns:
        str: The model's response.
    """
    # Create a filter instance
    filter_model = FilterLLM(
        model=model,
        prompt_store=prompt_store,
    )
    # Create the critic instance
    critic_model = CriticLLM(
        model=model,
        prompt_store=prompt_store,
    )
    # Create the retrieval model instance
    retrieval_model = RetrievalLLM(
        model=model,
        prompt_store=prompt_store,
        config=config,
    )
    # Start the timer and chat message
    start_time = time.time()
    answer_accepted, num_retries = False, 0
    thinking_response = gr.ChatMessage(
        content="⚙️ Processing...",
        metadata={
            "title": "🧠 Thinking...",
            "status": "pending",
            "role": "assistant",
        },
    )
    yield [thinking_response]

    # Filter the message to block unwanted conversations
    message_with_history = "\n\n".join(
        [
            f"{item['role']}: {item['content']}"
            for item in history + [{"role": "user", "content": message}]
        ]
    )
    filter_result = filter_model.filter(message=message_with_history)
    if not filter_result:
        # If the message is filtered, return the filter result
        response = gr.ChatMessage(
            content=random.choice(STANDARD_RESPONSES).format(
                STATION_NAME=config.constants.station_name,
                KONTAKT_LINK=config.constants.contact_link,
            ),
        )
        thinking_response.metadata["status"] = "done"
        thinking_response.metadata["title"] = "⛔ Nachricht blockiert."
        thinking_response.content = "⚠️ Nachricht blockiert."
        yield [thinking_response, response]
        return

    # Get the context from the database if needed
    # run the retriever to get the context
    context_dict: Dict = retrieval_model.get_context(
        query=message,
        date_today=DATE_TODAY,
        last_chunk_timestamp=LAST_CHUNK_TIMESTAMP,
        retriever=retriever,
    )

    context = format_context(context_dict)
    # Add the context to the context memory
    context_memory.add_context(context_dict)
    # Check if the model needs context
    if context:
        title = "ℹ️ Weitere Informationen werden verwendet."
    else:
        title = "ℹ️ Keine weiteren Informationen notwendig."

    # prepare context to be printed in the application
    # we need to remove all pseudo html tags <> and </> from the context with regex
    print_context = re.sub(r"<[^>]+>", "", context)
    thinking_response = gr.ChatMessage(
        content=f"Context:\n{print_context.strip()}",
        metadata={
            "title": title,
            "status": "done",
            "role": "assistant",
            "thinking": False,
        },
    )
    response = gr.ChatMessage(content="", metadata={"role": "assistant"})
    yield [thinking_response, response]

    # Generate the answer and run the critic in a loop until the answer is accepted or the maximum number of retries is reached
    previous_message, feedback_message = "", ""
    while not answer_accepted and num_retries < 3:
        # full_context = context_memory.get_context()
        # Generate the response
        for generation in generate_answer(
            history=history,
            message=message,
            context=context,
            model=model,
            previous_message=previous_message,
            feedback_message=feedback_message,
        ):
            response.content = generation
            yield [thinking_response, add_tooltips(response, context_dict)]
        previous_message = f"Abgelehnte Antwort:\n{generation}\n"

        thinking_response.metadata["status"] = "done"
        thinking_response.metadata["title"] = "🟢 Antwort generiert."
        thinking_response.metadata["duration"] = time.time() - start_time
        response.content = generation
        yield [thinking_response, add_tooltips(response, context_dict)]

        # ask the critique for feedback and display the response
        history_str = "\n\n".join(
            [
                f"{item['role']}: {item['content']}"
                for item in history + [{"role": "user", "content": message}]
            ]
        )

        feedback = critic_model.give_feedback(
            query=history_str,
            answer=generation,
            context=context,
        )
        critique_response = gr.ChatMessage(
            content=feedback.raw_feedback,
            metadata={
                "title": "🤓 Feedback zur Antwort",
                "id": 2,
                "status": "done",
                "role": "assistant",
                "thinking": False,
            },
        )
        yield [
            thinking_response,
            add_tooltips(response, context_dict),
            critique_response,
        ]
        if feedback:
            # Check if the feedback is positive
            if feedback.accepted:
                answer_accepted = True
                critique_response.metadata["title"] = "✅ Antwort akzeptiert."
                critique_response.metadata["thinking"] = False
            else:
                # If the feedback is negative, retry the generation
                num_retries += 1
                critique_response.metadata["title"] = (
                    "🔁 Antwort abgelehnt. Erneuter Versuch..."
                )
                feedback_message = "{reason}".format(reason=feedback.message)
            critique_response.metadata["status"] = "done"
    yield [thinking_response, add_tooltips(response, context_dict), critique_response]


custom_head = """
<!-- Basic tags -->
<title>RadioBrain Chatbot Demo</title>
<meta name="description"
      content="RadioBrain allows you to chat with the live radio program of a local radio station.">
"""


custom_login_html = """
<div style="text-align:center; margin: 1rem 0">
  <h1>Willkommen bei RadioBrain</h2>
</div>
"""


@click.command()
@click.option("--config", help="Path to the configuration file.", required=True)
def main(config: str):
    """Main function to start the Gradio app.

    Args:
        config (str): Path to the configuration file.
    """
    # Load the configuration file if provided
    config = AppConfig.from_yaml(path=config)

    initialize(config=config)

    with gr.Blocks(
        title="RadioBrain Chat",
        analytics_enabled=False,
        head=custom_head,
        css_paths="assets/components.css",
        css="#title {text-align:center;}",
        fill_height=True,
        theme=theme,
    ) as app:
        with gr.Sidebar(open=True, width="20%"):
            gr.HTML(
                f"""<h1>RadioBrain Chatbot</h1>
                <div style="font-size:1.2em;">Ein Chatbot, der Fragen zum aktuellen <b>Live-Radioprogramm von {config.constants.station_name}</b> beantwortet.</div>
                <br>
                <div style="font-size:1.2em;">Der Live-Betrieb ist hier simuliert und gerade ist <b>{LAST_CHUNK_TIMESTAMP.split(" ")[-1]} Uhr</b>.</div>

                <h3>Ein Prototype von</h3>"""
            )

            gr.Image(
                value="assets/RZ_Logo_KIM_RGB_D-Blau.png",
                type="filepath",
                show_download_button=False,
                show_label=False,
                show_fullscreen_button=False,
            )

        bot = gr.Chatbot(
            label="RadioBot",
            show_label=False,
            type="messages",
            scale=1,
            height="80vh",
            show_copy_button=True,
            avatar_images=(
                None,
                "https://em-content.zobj.net/source/twitter/53/robot-face_1f916.png",
            ),
        )

        def on_clear():
            # Clear the context memory
            context_memory.clear_context()

        bot.clear(on_clear)

        with gr.Row():
            with gr.Column(
                scale=1,
                elem_id="chatcol",
            ):
                gr.ChatInterface(
                    fn=partial(process_message, config=config),
                    type="messages",
                    chatbot=bot,
                    analytics_enabled=False,
                    show_progress=True,
                    flagging_mode="manual",
                    textbox=gr.Textbox(
                        submit_btn=True, placeholder="Stell deine Frage...", type="text"
                    ),
                    fill_height=True,
                    editable=True,
                    run_examples_on_click=True,
                    api_name=False,  # Disable API endpoint generation
                )  # .render()

    # Access the underlying FastAPI app and add CORS middleware.
    app.app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # manage authentication if username and password are set in the config
    if config.auth.username and config.auth.password:
        auth = [(config.auth.username, config.auth.password)]
    else:
        auth = None

    app.launch(
        share=config.run.share,
        debug=config.run.debug,
        favicon_path="assets/favicon.ico",
        auth=auth,
        auth_message=custom_login_html,
    )


if __name__ == "__main__":
    main()
