import pandas as pd
from tqdm import tqdm

from llm.models import get_model
from config_utils import EvalConfig
from app import process_message, initialize


HELPFULNESS_JUDGE_PROMPT = """
You are a helpful assistant that evaluates the helpfulness of responses to user queries.
Your task is to rate the helpfulness of the response on a scale from 0 to 5, where:
- 0 means the response is completely unhelpful and does not address the query at all.
- 1 means the response is minimally helpful, providing very little relevant information.
- 2 means the response is somewhat helpful, addressing the query but lacking depth or detail.
- 3 means the response is moderately helpful, providing a good amount of relevant information.
- 4 means the response is very helpful, addressing the query thoroughly and providing useful information.
- 5 means the response is extremely helpful, providing comprehensive and detailed information that fully addresses the query.

Please evaluate the following response to the query and provide a helpfulness score from 0 to 5:
Query:
{query}

Response: 
{response}

Answer with a single number, the helpfulness score from 0 to 5.
"""

ANSWER_RELEVANCE_JUDGE_PROMPT = """
You are a helpful assistant that evaluates the relevance of answers to user queries.
Your task is to rate the relevance of the answer on a scale from 0 to 5, where:
- 0 means the answer is completely irrelevant and does not address the query at all.
- 1 means the answer is minimally relevant, providing very little information related to the query.
- 2 means the answer is somewhat relevant, addressing the query but lacking depth or detail.
- 3 means the answer is moderately relevant, providing a good amount of information related to the query.
- 4 means the answer is very relevant, addressing the query thoroughly and providing useful information.
- 5 means the answer is extremely relevant, providing comprehensive and detailed information that fully addresses the query.

Please evaluate the following answer to the query and provide a relevance score from 0 to 5:
Query:
{query}

Answer:
{answer}

Answer with a single number, the relevance score from 0 to 5.
"""


def get_score(
    prompt: str, model_name: str, base_url: str, temperature: float = 0.0
) -> int:
    """
    Get the score from the model based on the provided prompt.

    Args:
        prompt (str): The prompt to send to the model.
        model_name (str): The name of the model to use.
        base_url (str): The base URL for the model API.
        temperature (float): The temperature for the model.

    Returns:
        int: The score returned by the model.
    """
    model = get_model(name=model_name, temperature=temperature, base_url=base_url)
    response = model.invoke([("human", prompt)])
    score = response.content.strip()
    try:
        return int(score)
    except ValueError:
        print(f"Invalid score received: {score}")
        return 0


def run_rag_test(config: EvalConfig):
    initialize(config)

    # Read the test messages from a CSV file
    test_queries = pd.read_csv(config.test_suite.eval_data_rag)

    helpfulness_scores = []
    answer_relevance_scores = []

    print(f"Running RAG test with {len(test_queries)} queries...")
    for _, row in tqdm(test_queries.iterrows(), total=len(test_queries)):
        message_text = row["query"]
        print(f"Testing message: {message_text}")

        # Process the message and get the response
        process_gen = process_message(message_text, history=[], config=config)
        for response in process_gen:
            pass
        # response = process_message(message_text, history=[], config=config)
        response = response[1]

        # Run the judge model to evaluate the helpfulness of the response
        helpfulness_score = get_score(
            HELPFULNESS_JUDGE_PROMPT.format(query=message_text, response=response),
            model_name=config.judge.model,
            temperature=config.judge.temperature,
        )
        helpfulness_scores.append(helpfulness_score)

        # Run the judge model to evaluate the relevance of the answer
        answer_relevance_score = get_score(
            ANSWER_RELEVANCE_JUDGE_PROMPT.format(query=message_text, answer=response),
            model_name=config.judge.model,
            temperature=config.judge.temperature,
        )
        answer_relevance_scores.append(answer_relevance_score)
        print(
            f"Helpfulness score: {helpfulness_score}, Answer relevance score: {answer_relevance_score}"
        )

    print("\nHelpfulness scores:")
    print(f"Mean: {sum(helpfulness_scores) / len(helpfulness_scores):.2f}")
    print(f"0: {helpfulness_scores.count(0)}")
    print(f"1: {helpfulness_scores.count(1)}")
    print(f"2: {helpfulness_scores.count(2)}")
    print(f"3: {helpfulness_scores.count(3)}")
    print(f"4: {helpfulness_scores.count(4)}")
    print(f"5: {helpfulness_scores.count(5)}")

    print()
    print("\nAnswer relevance scores:")
    print(f"Mean: {sum(answer_relevance_scores) / len(answer_relevance_scores):.2f}")
    print(f"0: {answer_relevance_scores.count(0)}")
    print(f"1: {answer_relevance_scores.count(1)}")
    print(f"2: {answer_relevance_scores.count(2)}")
    print(f"3: {answer_relevance_scores.count(3)}")
    print(f"4: {answer_relevance_scores.count(4)}")
    print(f"5: {answer_relevance_scores.count(5)}")
