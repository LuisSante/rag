import os
from pathlib import Path
from typing import List
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.schema import Document


class DocumentLoader:
    def load(self, directory: str | Path) -> List[Document]:
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        loader = PyPDFDirectoryLoader(str(directory))
        documents = loader.load()
        if not documents:
            raise ValueError(f"Nenhum PDF válido encontrado em: {directory}")
        return documents