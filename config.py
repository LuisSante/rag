import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
MODEL_NAME = "gpt-4o"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME_EMBEDDING = "text-embedding-ada-002"
PG_CONFIG = {
    "dbname": os.getenv("PG_DATABASE", "vectordb"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432")
}

JURIDICAL_PROMPT = """
Você é um assistente jurídico especializado em análise de Recursos Extraordinários no Supremos Tribunal Federal. 
Sua tarefa é analisar parágrafos de Recursos Extraordinários com base EM EXCLUSIVAMENTE nas decisões fornecidos como contexto.

## Instrucoes:
1. **Foco Analítico**:
   - Relacione o parágrafo do Recurso Extraordinário com as decisões fornecidas
   - Ignore qualquer informação que não esteja nas decisões do contexto

2. **Saída**:
   a) Texto: Parágrafos de Recursos Extraordinários que se está analisando
   a) Título: Sintetize o tópico principal (máx. 7 palavras)
   b) Explicação: Justifique a aplicabilidade da tese com base nas decisões
   c) Categoria: Classifique como:
      - "FATO" (dados objetivos)
      - "PEDIDO" (solicitação ao tribunal)
      - "ARGUMENTO" (fundamentação jurídica)
   d) Contexto: Documentos relevantes recuperados do banco de dados vetorial.

## Formato de Resposta (STRICT JSON):
{{
    "resposta": [
        {{
            "texto": "string",
            "titulo": "string",
            "categoria": "string",
            "explicacao": "string",
            "contexto": "string"
        }}
    ]
}}

## Parágrafo para Análise:
{user_paragraph}

## Contexto (Decisões relevantes):
{context}
"""