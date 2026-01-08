from tqdm import tqdm

from config_utils import EvalConfig
from filtering import FilterLLM
from llm.models import get_model
from llm.prompt_management import PromptStore


def initialize(config: EvalConfig):
    # Initialize the prompt store
    prompt_store = PromptStore(config=config)

    # Initialize the model
    model = get_model(
        name=config.model.name,
        temperature=config.model.temperature,
        base_url=config.model.base_url,
    )
    # Create a filter instance
    filter_model = FilterLLM(
        model=model,
        prompt_store=prompt_store,
    )
    return filter_model


def read_csv(file_path: str) -> str:
    """
    Read a CSV file and return its content as list of dictionaries.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    # Assuming the first line is the header and the rest are data rows
    header = lines[0].strip().split(",")
    data = []
    for line in lines[1:]:
        values = line.strip().split(",")
        data.append(dict(zip(header, values)))
    return data


def run_red_teaming_test(config: EvalConfig):
    """
    Run a red teaming test to check if the filter model blocks unwanted messages.
    """
    # initialize the model
    filter_model = initialize(config)

    # Read the test messages from a CSV file
    test_queries = read_csv(config.test_suite.eval_data_red_teaming)

    fp, fn, tp, tn = 0, 0, 0, 0
    # Iterate through each message and check if it is filtered
    print(f"Running red teaming test with {len(test_queries)} queries...")
    for row in tqdm(test_queries):
        message_text = row["query"]
        print(f"Testing message: {message_text}")
        # catch warnings
        is_allowed = filter_model.filter(message=message_text)
        print(f"Message allowed: {is_allowed}")
        print(f"Expected: {row['allowed']}")

        # collect metrics
        if is_allowed and row["allowed"] == "True":
            tp += 1
        elif not is_allowed and row["allowed"] == "False":
            tn += 1
        elif is_allowed and row["allowed"] == "False":
            fp += 1
        elif not is_allowed and row["allowed"] == "True":
            fn += 1
        print("-" * 50)
    print()
    # Print the results
    print("Red Teaming Test Results:")
    print(f"True Positives (TP): {tp}")
    print(f"True Negatives (TN): {tn}")
    print(f"False Positives (FP): {fp}")
    print(f"False Negatives (FN): {fn}")
    print(f"Accuracy: {(tp + tn) / (tp + tn + fp + fn) * 100:.2f}%")
    print(f"Precision: {tp / (tp + fp) * 100:.2f}%")
    print(f"Recall: {tp / (tp + fn) * 100:.2f}%")
    print(f"F1 Score: {2 * tp / (2 * tp + fp + fn) * 100:.2f}%")
