import os
from langchain_openai import ChatOpenAI


def get_model(
    name: str = "gpt-oss:120b",
    temperature: float = 0,
    base_url: str = None,
    api_key: str = "***",
    num_ctx: int = 8162,
    num_predict: int = 1024,
) -> ChatOpenAI:
    """
    Get the model based on the type.

    Args:
        name (str): The name of the model to use.
            Options: "gpt-oss:120b", "gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4.1-mini".
        temperature (float): The temperature for the model.
        base_url (str): The base URL for the model API.
        api_key (str): The API key for the model. Optional.
        num_ctx (int): The number of context tokens.
        num_predict (int): The number of prediction tokens.
    Returns:
        ChatOpenAI: The initialized model client.
    """
    extra_body = {
        "options": {
            "num_ctx": num_ctx,
            "num_predict": num_predict,
        }
    }

    if name == "gpt-oss:120b":
        model_name = "gpt-oss:120b"
        key = "***"
    elif name in ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4.1-mini"]:
        return ChatOpenAI(
            model=name,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url,
        )
    else:
        raise ValueError(
            f"Model {name} not supported. Please choose from: gpt-oss:120b, gpt-4o-mini, gpt-4o, gpt-4.1, gpt-4.1-mini."
        )
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=key,
        base_url=base_url,
        extra_body=extra_body,
    )
