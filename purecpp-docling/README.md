
# Docling PureCPP Wrapper

This document describes how to use the Python wrapper for the Docling PureCPP project.

## Description

The `docling-purecpp` project provides a high-performance document loading and processing solution by leveraging a C++ backend with Python bindings. This wrapper allows you to easily integrate the power of Docling into your Python applications.

## Installation

As this project involves a C++ backend, it needs to be compiled first. Follow the build instructions in the main project's README to generate the necessary library files.

## Usage

### Basic Usage

Basic usage of `DoclingLoader` looks as follows:

```python
from purecpp_libs import DoclingLoader, RAGDocument

# Can be a local file path, or a list of paths
FILE_PATH = ["/path/to/your/document.pdf", "/path/to/another/document.docx"]

loader = DoclingLoader(file_path=FILE_PATH)

# The lazy_load() method returns a generator
docs_generator = loader.lazy_load()
for doc in docs_generator:
    print(f"Content: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")
    print("---")
```

### Advanced Usage

When initializing a `DoclingLoader`, you can use the following parameters:

- `file_path`: A string or a list of strings representing the path(s) to the source file(s).
- `converter` (optional): A specific Docling `DocumentConverter` instance to use.
- `convert_kwargs` (optional): A dictionary of keyword arguments for the conversion process.
- `export_type` (optional): The export mode to use. Can be `ExportType.DOC_CHUNKS` (default) or `ExportType.MARKDOWN`.
- `md_export_kwargs` (optional): A dictionary of keyword arguments for Markdown exporting.
- `chunker` (optional): A specific Docling `BaseChunker` instance to use (for document-chunk mode).
- `meta_extractor` (optional): A specific metadata extractor to use.

#### Example with Custom Configuration

```python
from purecpp_libs import DoclingLoader, ExportType
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

# Custom converter configuration
converter = DocumentConverter()
convert_kwargs = {"do_ocr": True, "do_table_structure": True}

# Custom chunker for document chunks
chunker = HybridChunker()

# Custom markdown export settings
md_export_kwargs = {"image_placeholder": "[IMAGE]"}

loader = DoclingLoader(
    file_path="/path/to/document.pdf",
    converter=converter,
    convert_kwargs=convert_kwargs,
    export_type=ExportType.DOC_CHUNKS,  # or ExportType.MARKDOWN
    md_export_kwargs=md_export_kwargs,
    chunker=chunker
)

for doc in loader.lazy_load():
    print(f"Content: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")
```

### Export Types

The loader supports two export types:

1. **`ExportType.DOC_CHUNKS`** (default): Exports documents as chunked content using the specified chunker
2. **`ExportType.MARKDOWN`**: Exports documents as markdown format

### Custom Metadata Extraction

You can provide a custom metadata extractor by implementing the `BaseMetadataExtractor` interface:

```python
from purecpp_libs import BaseMetadataExtractor
import json

class CustomMetadataExtractor(BaseMetadataExtractor):
    def extract_chunk_meta(self, file_path, chunk):
        return {
            "source": file_path,
            "chunk_type": chunk.meta.type if hasattr(chunk.meta, 'type') else "unknown",
            "dl_meta": json.dumps(chunk.meta.export_json_dict())
        }
    
    def extract_dl_doc_meta(self, file_path, dl_doc):
        return {
            "source": file_path,
            "document_title": dl_doc.title if hasattr(dl_doc, 'title') else "Unknown"
        }

loader = DoclingLoader(
    file_path="/path/to/document.pdf",
    meta_extractor=CustomMetadataExtractor()
)
```

## API Reference

### DoclingLoader

The main class for loading and processing documents.

**Parameters:**
- `file_path` (Union[str, Iterable[str]]): Path(s) to the source file(s)
- `converter` (Optional[DocumentConverter]): Custom document converter instance
- `convert_kwargs` (Optional[Dict[str, Any]]): Arguments for the conversion process
- `export_type` (ExportType): Export format (DOC_CHUNKS or MARKDOWN)
- `md_export_kwargs` (Optional[Dict[str, Any]]): Arguments for markdown export
- `chunker` (Optional[BaseChunker]): Custom chunker for document chunks mode
- `meta_extractor` (Optional[BaseMetadataExtractor]): Custom metadata extractor

**Methods:**
- `lazy_load()`: Returns a generator that yields `RAGDocument` objects

### RAGDocument

Represents a processed document with content and metadata.

**Attributes:**
- `page_content` (str): The processed content of the document/chunk
- `metadata` (Dict): Metadata associated with the document/chunk