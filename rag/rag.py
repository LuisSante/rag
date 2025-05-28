# RAG (Retrieval-Augmented Generation)
# Retrieval (Recuperação): Procura de informação relevante em uma base de dados
# Augmenteed Generation (Geração Aumentada): Modelo de LLM (gpt-4o) gera respostas utilizando a informação recuperada.

"""
Sistema RAG para análise jurídica de Recursos Extraordinários do STF.
Recupera acórdãos relevantes e gera análises com GPT-4.
"""

from pathlib import Path
import asyncio
import argparse
from rag.utils_rag import RAGSystem

def run_rag():
    try:

        # Configuración de argumentos
        parser = argparse.ArgumentParser(description="RAG system for legal analysis")
        parser.add_argument("--tema", type=int, default=663)
        parser.add_argument("--csv", type=str, default="313894299")
        parser.add_argument("--output", type=str, help="Custom name for the output file")
        args = parser.parse_args()

        print("[SYSTEM] Initializing RAG components...")

        # Utilizar os argumentos proporcionados
        num_tema = args.tema
        num_csv = args.csv
        output_json = args.output if args.output else f'Testes/resultado_{num_csv}_{num_tema}.json'


        input_csv = f'Testes/{num_csv}.csv'

        rag = RAGSystem()
        retriever, llm = rag.initialize_components(num_tema)
        chain = rag.create_chain(retriever, llm)
                
        if not Path(input_csv).exists():
            raise FileNotFoundError(f"Input file {input_csv} not found")

        print("[SYSTEM] Starting analysis...")
        asyncio.run(rag.process_csv_file(input_csv, output_json, chain))
        print(f"[SYSTEM] Analysis completed successfully! Save in: {output_json}")
    
    except Exception as e:
        print(f"[SYSTEM CRITICAL ERROR] {str(e)}")
        exit(1)