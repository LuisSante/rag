import json
import re
import pandas as pd
import asyncio
import psycopg2
from concurrent.futures import ThreadPoolExecutor
from typing import List
from psycopg2 import sql
from psycopg2.extras import DictCursor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from config import OPENAI_API_KEY, PG_CONFIG, JURIDICAL_PROMPT, MODEL_NAME

class PostgreSQLRetriever(BaseRetriever):
    """Retriever implementation for PostgreSQL with pgvector"""
    
    embeddings: OpenAIEmbeddings
    collection_name: str
    k: int = 5

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """Retrieve relevant documents from PostgreSQL"""
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query_embedding = self.embeddings.embed_query(query)
                
                search_query = sql.SQL("""
                SELECT content, metadata
                FROM {}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """).format(sql.Identifier(self.collection_name))
                
                cur.execute(search_query, (query_embedding, self.k))
                results = cur.fetchall()
                
                return [
                    Document(
                        page_content=row['content'],
                        metadata=row['metadata']
                    ) for row in results
                ]
        except Exception as e:
            print(f"[ERROR] Error retrieving documents: {str(e)}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()

class RAGSystem:
    """Main RAG system class"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")

    def initialize_components(self, theme_number: int):
        """Initialize RAG components for a specific theme"""
        try:
            embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=OPENAI_API_KEY)
            
            retriever = PostgreSQLRetriever(
                embeddings=embeddings,
                collection_name=f"tema_{theme_number}",
                k=5
            )

            llm = ChatOpenAI(
                model=MODEL_NAME,
                temperature=0,
                openai_api_key=OPENAI_API_KEY
            )

            return retriever, llm
        except Exception as e:
            raise RuntimeError(f"Failed to initialize components: {str(e)}")

    def create_chain(self, retriever, llm):
        """Create the RAG processing pipeline"""
        prompt = ChatPromptTemplate.from_template(JURIDICAL_PROMPT)
        return (
            {
                "context": lambda x: retriever.invoke(x["user_paragraph"]),
                "user_paragraph": lambda x: x["user_paragraph"]
            }
            | prompt
            | llm
            | StrOutputParser()
        )

    def parse_json_response(self, response):
        """Parse and validate the JSON response"""
        cleaned = re.sub(r'```json|```', '', response).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON response: {str(e)}")
            print(f"[DEBUG] Raw response: {response[:200]}...")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected parsing error: {str(e)}")
            return None

    def analyze_paragraph(self, df, chain):
        """Process a paragraph through the RAG chain"""
        try:
            response = chain.invoke({"user_paragraph": df["clean_text"]})
            return df["paragraph_enum"], self.parse_json_response(response)
        except Exception as e:
            print(f"[ERROR] Processing failed for paragraph: {str(e)}")
            return None

    async def process_paragraphs_async(self, df, chain) -> list:
        """Process multiple paragraphs in parallel"""
        with ThreadPoolExecutor(max_workers=2) as executor:
            loop = asyncio.get_event_loop()
            tasks = []

            for index, row in df.iterrows():
                task = loop.run_in_executor(
                    executor,
                    lambda p: self.analyze_paragraph(p, chain),
                    row
                )
                tasks.append(task)
            
            return await asyncio.gather(*tasks)

    async def process_csv_file(self, input_csv: str, output_json: str, chain) -> None:
        """Process CSV file and generate JSON output"""
        df = pd.read_csv(input_csv, sep=";", low_memory=False)
        df = pd.DataFrame({
            'paragraph_enum': range(1, len(df) + 1),
            'clean_text': df['text'].str.replace('\n', ' ').str.strip()
        })

        analyses = await self.process_paragraphs_async(df, chain)

        results = []
        for analysis in analyses:
            if analysis is not None:
                index, parsed = analysis
                if parsed and 'resposta' in parsed and len(parsed['resposta']) > 0:
                    results.append({
                        "paragraph_enum": index,
                        "text": parsed['resposta'][0].get("texto", ""),
                        "titulo": parsed['resposta'][0].get("titulo", ""),
                        "categoria": parsed['resposta'][0].get("categoria", ""),
                        "explicacao": parsed['resposta'][0].get("explicacao", ""),
                        "contexto": parsed['resposta'][0].get("contexto", "")
                    })

        with open(output_json, 'w', encoding='utf-8') as json_file:
            json.dump(results, json_file, indent=2, ensure_ascii=False)