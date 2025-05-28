from __future__ import annotations

import logging
from typing import List, Dict
from psycopg2.extras import DictCursor

from config import PG_CONFIG
from .postgres import PostgresSaver

log = logging.getLogger(__name__)


class DBStats:
    @staticmethod
    def get_vector_tables_with_stats() -> List[Dict[str, str | int]]:
        try:
            with PostgresSaver._get_connection() as conn, conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(
                    """
                    SELECT 
                        t.table_name,
                        pg_size_pretty(pg_total_relation_size('"' || t.table_name || '"')) AS size,
                        (xpath('/row/cnt/text()', query_to_xml(format('SELECT COUNT(*) as cnt FROM %I', t.table_name), false, true, '')))[1]::text::int AS row_count
                    FROM information_schema.tables t
                    JOIN information_schema.columns c ON t.table_name = c.table_name
                    WHERE t.table_schema = 'public'
                      AND c.data_type = 'USER-DEFINED'
                      AND c.udt_name = 'vector'
                    GROUP BY t.table_name;
                    """
                )
                return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            log.error("Erro ao listar tabelas: %s", str(e))
            return []

    @staticmethod
    def print_table_stats():
        tables = DBStats.get_vector_tables_with_stats()
        if not tables:
            print("Nenhuma tabela vetorial encontrada.")
            return

        print("\nTabelas com embeddings vetoriais no PostgreSQL:")
        print("{:<30} {:<15} {:<10}".format("Nome", "Tamanho", "Registros"))
        print("-" * 55)
        for tbl in tables:
            print("{:<30} {:<15} {:<10}".format(tbl["table_name"], tbl["size"], tbl["row_count"]))
