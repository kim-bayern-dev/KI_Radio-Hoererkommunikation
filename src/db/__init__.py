from langchain_ollama import OllamaEmbeddings


MODEL = None


def _get_embedding_model(embedding_model: str, base_url: str) -> OllamaEmbeddings:
    global MODEL
    if MODEL:
        return MODEL
    MODEL = OllamaEmbeddings(model=embedding_model, base_url=base_url)
    return MODEL
