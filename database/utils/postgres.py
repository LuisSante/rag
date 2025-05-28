from __future__ import annotations

import json
import logging
from typing import List, Dict, Any
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values, DictCursor
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

from config import PG_CONFIG

log = logging.getLogger(__name__)


class PostgresSaver:
    """Gestiona la conexión y el guardado de documentos vectorizados."""

    def __init__(self, model_name: str, api_key: str | None):
        self.model_name = model_name
        self.api_key = api_key
        self.embedding_model = OpenAIEmbeddings(model=model_name, openai_api_key=api_key)

    # ---------------------------------------------------------------------
    # Conexión y helpers
    # ---------------------------------------------------------------------
    @staticmethod
    def _get_connection():
        return psycopg2.connect(**PG_CONFIG)

    @staticmethod
    def check_table_exists(collection_name: str) -> bool:
        """Comprueba si la tabla existe en la DB."""
        try:
            with PostgresSaver._get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM pg_tables
                        WHERE schemaname = 'public'
                          AND tablename = %s
                    );
                    """,
                    (collection_name,),
                )
                return cur.fetchone()[0]
        except Exception as e:
            log.error("Erro ao verificar tabela %s: %s", collection_name, str(e))
            return False

    @staticmethod
    def _create_collection_table(conn, collection_name: str):
        """Crea la tabla e índice HNSW si no existen."""
        with conn.cursor() as cur:
            create_table_query = sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    metadata JSONB,
                    embedding VECTOR(1536),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            ).format(table_name=sql.Identifier(collection_name))

            create_index_query = sql.SQL(
                """
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} USING hnsw (embedding vector_cosine_ops);
                """
            ).format(
                index_name=sql.Identifier(f"{collection_name}_embedding_idx"),
                table_name=sql.Identifier(collection_name),
            )

            cur.execute(create_table_query)
            cur.execute(create_index_query)
            conn.commit()

    # ------------------------------------------------------------------
    # Guardado principal
    # ------------------------------------------------------------------
    def save(self, chunks: List[Document], collection_name: str, overwrite: bool = False) -> str:
        """Genera embeddings y los guarda en PostgreSQL."""
        with PostgresSaver._get_connection() as conn:
            if overwrite and PostgresSaver.check_table_exists(collection_name):
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("DROP TABLE IF EXISTS {};").format(sql.Identifier(collection_name)))
                    conn.commit()
                    log.info("Tabla existente removida: %s", collection_name)

            # Crear tabla (si no existe)
            PostgresSaver._create_collection_table(conn, collection_name)

            # Generar embeddings
            documents: list[tuple[str, str]] = []  # (content, metadata_json)
            embeddings: list[list[float]] = []

            for chunk in chunks:
                content = chunk.page_content
                metadata_json = json.dumps(chunk.metadata)
                embedding_vector = self.embedding_model.embed_query(content)
                documents.append((content, metadata_json))
                embeddings.append(embedding_vector)

            data = [
                (doc[0], doc[1], emb) for doc, emb in zip(documents, embeddings)
            ]

            insert_query = sql.SQL(
                """
                INSERT INTO {} (content, metadata, embedding)
                VALUES %s
                """
            ).format(sql.Identifier(collection_name))

            with conn.cursor() as cur:
                execute_values(cur, insert_query, data, template="(%s, %s::jsonb, %s::vector)")
                log.info("Salvos %d chunks na tabela '%s'", len(chunks), collection_name)

        return collection_name
