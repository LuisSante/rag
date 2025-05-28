from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from config import MODEL_NAME_EMBEDDING, OPENAI_API_KEY
from .utils.documents import DocumentLoader
from .utils.splitter import TextSplitter
from .utils.postgres import PostgresSaver
from .utils.stats import DBStats

log = logging.getLogger(__name__)


class DatabaseProcessor:

    def __init__(
        self,
        model_name: str = MODEL_NAME_EMBEDDING,
        api_key: str | None = OPENAI_API_KEY,
        chunk_size: int = 500,
        chunk_overlap: int = 200,
    ):
        if api_key is None:
            raise ValueError("OPENAI_API_KEY must be set in environment or .env file")

        self.loader = DocumentLoader()
        self.splitter = TextSplitter(chunk_size, chunk_overlap)
        self.saver = PostgresSaver(model_name, api_key)

    # ------------------------------------------------------------------
    # Procesamiento
    # ------------------------------------------------------------------
    def process_theme(self, data_path: str | Path, overwrite: bool = False):
        data_path = Path(data_path)
        collection_name = f"tema_{data_path.name}"

        docs = self.loader.load(data_path)
        chunks = self.splitter.split(docs)
        self.saver.save(chunks, collection_name, overwrite=overwrite)
        log.info("Tema %s processado com sucesso", data_path.name)

    def process_all_themes(self, base_path: str | Path = "Acordaos/"):
        base_path = Path(base_path)
        if not base_path.exists():
            raise FileNotFoundError(f"Diretório não encontrado: {base_path}")

        processed: List[str] = []
        failed: List[str] = []

        for theme_folder in sorted(p for p in base_path.iterdir() if p.is_dir() and p.name.isdigit()):
            print(f"\n{'=' * 50}\nProcessando tema {theme_folder.name}...")
            try:
                overwrite = self.saver.check_table_exists(f"tema_{theme_folder.name}")
                self.process_theme(theme_folder, overwrite=overwrite)
                processed.append(theme_folder.name)
            except Exception as e:
                failed.append(theme_folder.name)
                log.error("Erro no tema %s: %s", theme_folder.name, str(e))

        print("\nResumo:")
        print(f"Temas processados: {len(processed)}")
        print(f"Temas com erro: {len(failed)}")

    # ------------------------------------------------------------------
    # Info DB
    # ------------------------------------------------------------------
    @staticmethod
    def print_db_info():
        DBStats.print_table_stats()
