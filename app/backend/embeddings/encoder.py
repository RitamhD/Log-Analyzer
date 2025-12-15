from app.backend.embeddings.transformer_model import EmbeddingModel


def encode_messages(messages: list[str]) -> list[list[float]]:
    model = EmbeddingModel.load()
    return model.encode(messages).tolist()