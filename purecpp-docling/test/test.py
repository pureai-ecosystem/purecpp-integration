import unittest
import tempfile
from pathlib import Path
import os
import sys



from loader import DoclingLoader, ExportType, BaseMetadataExtractor
from docling.chunking import BaseChunk
from docling_core.types.doc.document import DoclingDocument


class TestDoclingLoader(unittest.TestCase):

    def setUp(self):
        """Set up a temporary file for testing."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.md')
        self.temp_file.write('This is a test document.')
        self.temp_file.close()
        self.file_path = self.temp_file.name

    def tearDown(self):
        """Clean up the temporary file."""
        os.remove(self.file_path)

    def test_markdown_export(self):
        """Test that the loader can export a document as markdown."""
        loader = DoclingLoader(self.file_path, export_type=ExportType.MARKDOWN, convert_kwargs={})
        docs = list(loader.lazy_load())
        self.assertEqual(len(docs), 1)
        self.assertIn('This is a test document.', docs[0].page_content)
        self.assertEqual(docs[0].metadata['source'], self.file_path)

    def test_doc_chunks_export(self):
        """Test that the loader can export a document as chunks."""
        loader = DoclingLoader(self.file_path, export_type=ExportType.DOC_CHUNKS, convert_kwargs={})
        docs = list(loader.lazy_load())
        self.assertGreater(len(docs), 0)
        self.assertIn('This is a test document.', docs[0].page_content)
        self.assertEqual(docs[0].metadata['source'], self.file_path)
        self.assertIn('dl_meta', docs[0].metadata)

    def test_custom_metadata_extractor(self):
        """Test that a custom metadata extractor can be used."""
        class CustomExtractor(BaseMetadataExtractor):
            def extract_chunk_meta(self, file_path: str, chunk: BaseChunk):
                return {'custom_key': 'chunk_value', 'path': file_path}

            def extract_dl_doc_meta(self, file_path: str, dl_doc: DoclingDocument):
                return {'custom_key': 'doc_value', 'path': file_path}

        # Test with doc chunks
        loader_chunks = DoclingLoader(
            self.file_path, 
            export_type=ExportType.DOC_CHUNKS, 
            meta_extractor=CustomExtractor(),
            convert_kwargs={}
        )
        docs_chunks = list(loader_chunks.lazy_load())
        self.assertEqual(docs_chunks[0].metadata['custom_key'], 'chunk_value')
        self.assertEqual(docs_chunks[0].metadata['path'], self.file_path)

        # Test with markdown
        loader_md = DoclingLoader(
            self.file_path, 
            export_type=ExportType.MARKDOWN, 
            meta_extractor=CustomExtractor(),
            convert_kwargs={}
        )
        docs_md = list(loader_md.lazy_load())
        self.assertEqual(docs_md[0].metadata['custom_key'], 'doc_value')
        self.assertEqual(docs_md[0].metadata['path'], self.file_path)

    def test_pdf_loader_markdown(self):
        """Test that the loader can fetch and process a document from an arXiv URL."""
        pdf_url = "https://arxiv.org/pdf/1706.03762.pdf" # Attention is all you need btw :)
        loader = DoclingLoader(
            file_path=pdf_url,
            export_type=ExportType.MARKDOWN,
        )
        docs = list(loader.lazy_load())
        self.assertGreater(len(docs), 0, "Loader should return at least one document.")
        self.assertIsInstance(docs[0].page_content, str)
        self.assertGreater(len(docs[0].page_content), 0, "Document page_content should not be empty.")
        self.assertEqual(docs[0].metadata['source'], pdf_url)

    def test_pdf_loader_doc_chunk(self):
        """Test that the loader can fetch and process a document from an arXiv URL."""
        pdf_url = "https://arxiv.org/pdf/1706.03762.pdf" # Attention is all you need btw :)
        loader = DoclingLoader(
            file_path=pdf_url,
            export_type=ExportType.DOC_CHUNKS,
        )
        docs = list(loader.lazy_load())
        self.assertGreater(len(docs), 0, "Loader should return at least one document.")
        self.assertIsInstance(docs[0].page_content, str)
        self.assertGreater(len(docs[0].page_content), 0, "Document page_content should not be empty.")
        self.assertEqual(docs[0].metadata['source'], pdf_url)

if __name__ == '__main__':
    unittest.main()
