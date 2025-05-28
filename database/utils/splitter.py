from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging

log = logging.getLogger(__name__)


class TextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            add_start_index=True,
        )

    def split(self, documents: List[Document]) -> List[Document]:
        chunks = self.splitter.split_documents(documents)
        log.info("Split %d documents into %d chunks.", len(documents), len(chunks))
        return chunks
