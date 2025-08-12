import torch
from transformers import AutoTokenizer, AutoModel
from typing import List

MODEL_ALIASES = {
    'bge-base': 'BAAI/bge-base-en-v1.5',
    'bge-large': 'BAAI/bge-large-en-v1.5',
    'mini-lm': 'sentence-transformers/all-MiniLM-L6-v2',
}

class HuggingFaceEmbeddings:
    """A pure Python embedding class using Hugging Face transformers.

    This class loads a pre-trained model from the Hugging Face Hub and uses it
    to generate sentence embeddings for a list of documents. It handles
    tokenization, model inference, and pooling.
    """
    def __init__(self, model_name: str = 'mini-lm', device: str = 'cpu'):
        """
        Initializes the embedding model.

        Args:
            model_name: The name or alias of the Hugging Face model to use.
            device: The device to run the model on ('cpu' or 'cuda').
        """
        # Resolve model alias if it exists
        model_id = MODEL_ALIASES.get(model_name, model_name)

        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModel.from_pretrained(model_id)
        self.device = device
        self.model.to(self.device)
        print(f"HuggingFaceEmbeddings model '{model_id}' loaded on {device}.")

    def _mean_pooling(self, model_output, attention_mask):
        """Performs mean pooling on the token embeddings.
        
        Takes the last hidden state and applies the attention mask to average the
        token embeddings across the sequence dimension.
        """
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask

    @torch.no_grad()
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of documents.

        Args:
            texts: A list of strings to embed.

        Returns:
            A list of embeddings, where each embedding is a list of floats.
        """
        print(f"Generating embeddings for {len(texts)} documents...")
        # Tokenize the input texts
        encoded_input = self.tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
        encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}

        # Get model output
        model_output = self.model(**encoded_input)

        # Perform pooling and normalization
        sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
        normalized_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

        print("Embeddings generated successfully.")
        return normalized_embeddings.tolist()


# Example usage:
if __name__ == '__main__':
    # Initialize the embedding model
    embeddings_model = HuggingFaceEmbeddings()

    # Define some sentences to embed
    sentences = [
        "This is an example sentence.",
        "Each sentence is converted to a vector."
    ]

    # Generate embeddings
    embeddings = embeddings_model.embed_documents(sentences)

    # Print the results
    for sentence, embedding in zip(sentences, embeddings):
        print(f"\nSentence: {sentence}")
        print(f"Embedding (first 5 dims): {embedding[:5]}...")
        print(f"Embedding dimension: {len(embedding)}")
