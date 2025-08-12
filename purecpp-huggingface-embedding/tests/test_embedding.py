import unittest
from purecpp_huggingface_embedding.embedding import HuggingFaceEmbeddings

class TestHuggingFaceEmbeddings(unittest.TestCase):

    def test_embed_documents(self):
        """Tests that embeddings are generated correctly."""
        embedder = HuggingFaceEmbeddings(model_name='mini-lm')
        texts = ["This is a test sentence.", "This is another test sentence."]
        embeddings = embedder.embed_documents(texts)
        
        # Check that we get a list of embeddings
        self.assertIsInstance(embeddings, list)
        # Check that we have one embedding per text
        self.assertEqual(len(embeddings), len(texts))
        # Check that the embeddings are of the correct type (list of floats)
        self.assertIsInstance(embeddings[0], list)
        self.assertIsInstance(embeddings[0][0], float)
        # Check the dimension of the embedding for the default model
        self.assertEqual(len(embeddings[0]), 384)

if __name__ == '__main__':
    unittest.main()
