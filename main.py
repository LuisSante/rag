import sys

def main():
    if not sys.argv[1:]:
        print("Uso: python main.py [db|rag] ...")
        return

    subcommand = sys.argv[1]
    args = sys.argv[2:]

    if subcommand == "db":
        from database.cli import main as db_main
        db_main(args)
    elif subcommand == "rag":
        from rag.rag import run_rag
        run_rag(*args)  # si acepta argumentos
    else:
        print(f"Comando desconhecido: {subcommand}")
        print("Uso: python main.py [db|rag] ...")

if __name__ == "__main__":
    main()
