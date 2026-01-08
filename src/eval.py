import click

from config_utils import EvalConfig
from test_suite.test_filter import run_red_teaming_test
from test_suite.test_rag import run_rag_test


@click.command()
@click.option(
    "--config",
    type=str,
    required=True,
    help="Path to the evaluation configuration file.",
)
def main(config: str):
    """
    Main entry point for the evaluation script.

    Args:
        config (str): Path to the evaluation configuration file.
    """
    print("Starting evaluation...")
    # Load the evaluation configuration
    config = EvalConfig.from_yaml(config)

    # Run the red teaming test
    if config.run_tests.red_teaming:
        print("Running red teaming test...")
        run_red_teaming_test(config=config)
        print("Red teaming test completed.")
        print()

    # Run the RAG test
    if config.run_tests.rag:
        print("Running RAG test...")
        run_rag_test(config=config)
        print("RAG test completed.")
        print()

    print("Evaluation completed.")


if __name__ == "__main__":
    main()
