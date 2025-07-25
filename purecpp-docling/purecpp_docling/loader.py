
"""Docling PureCPP loader module"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Iterable, Iterator, Optional, Union

import logging 

import json
from pathlib import Path

from purecpp_extract import BaseDataLoader 
from purecpp_libs import RAGDocument

from docling.chunking import BaseChunk, BaseChunker, HybridChunker
from docling_core.types.doc.document import DoclingDocument
from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


class ExportType(str, Enum):
    """Enumeration of available types to export to."""
    MARKDOWN = "markdown"
    DOC_CHUNKS = "doc_chunks"

class BaseMetadataExtractor(ABC):
    
    def extract_chunk_meta(self, file_path: Optional[str], chunk: BaseChunk):
        """Extract chunk metadata"""
        raise  NotImplementedError()

    def extract_dl_doc_meta(self, file_path: str, dl_doc: DoclingDocument):
        """Extract Docling document metadata"""
        raise NotImplementedError()


class MetadataExtractor(BaseMetadataExtractor):
    def extract_chunk_meta(self, file_path: Optional[str], chunk: BaseChunk ):
        return {
            "source": file_path,
            "dl_meta": json.dumps(chunk.meta.export_json_dict())
        }
    def extract_dl_doc_meta(self, file_path: str, dl_doc: DoclingDocument):
        return {"source": file_path}

class DoclingLoader(BaseDataLoader):
    """Docling loader"""
    def __init__(self, file_path: Union[str, Iterable[str]], *, converter: Optional[DocumentConverter] = None, convert_kwargs: Optional[Dict[str, Any]] = None, export_type: ExportType = ExportType.DOC_CHUNKS, md_export_kwargs: Optional[Dict[str, Any]] = None, chunker: Optional[BaseChunker] = None, meta_extractor: Optional[BaseMetadataExtractor] = None):
        super().__init__(1)

        self._file_paths = (file_path if isinstance(file_path, Iterable) and not isinstance(file_path, str) else [file_path])
        self._converter: DocumentConverter = converter or DocumentConverter()
        self._convert_kwargs = convert_kwargs if convert_kwargs is not None else {}
        self._export_type = export_type
        self._md_export_kwargs = (md_export_kwargs if md_export_kwargs is not None else{"image_placeholder": ""})

        if self._export_type == ExportType.DOC_CHUNKS:
            self._chunker: BaseChunker = chunker or HybridChunker()
        self._meta_extractor = meta_extractor or MetadataExtractor()
        

    def lazy_load(self):
        """Lazy load documents """
        logger.info(f"Processing files: {self._file_paths}")
        for file_path in self._file_paths:
            conv_res = self._converter.convert(source=file_path, **self._convert_kwargs)
            dl_doc = conv_res.document

            if self._export_type == ExportType.MARKDOWN:
                yield RAGDocument(
                    page_content=dl_doc.export_to_markdown(**self._md_export_kwargs),
                    metadata=self._meta_extractor.extract_dl_doc_meta(
                        file_path=file_path,
                        dl_doc=dl_doc,
                    ),
                )
            elif self._export_type == ExportType.DOC_CHUNKS:
                chunk_iter = self._chunker.chunk(dl_doc)
                for chunk in chunk_iter:
                    yield RAGDocument(
                        page_content=self._chunker.contextualize(chunk=chunk),
                        metadata=self._meta_extractor.extract_chunk_meta(
                            file_path=file_path,
                            chunk=chunk,
                        ),
                    )
            else:
                raise ValueError(f'Unexpected export type: {self._export_type}')

