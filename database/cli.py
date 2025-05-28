import argparse
import sys
import os
from .processor import DatabaseProcessor


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create PostgreSQL vector DB from PDF documents."
    )
    parser.add_argument(
        "--data_path",
        type=str,
        default=os.getenv("DATA_PATH", "Acordaos/339/"),
        help="Path to the folder containing PDFs of a single theme.",
    )
    parser.add_argument("--chunk_size", type=int, default=500)
    parser.add_argument("--chunk_overlap", type=int, default=200)
    parser.add_argument(
        "--overwrite",
        type=str,
        default="False",
        help="Overwrite existing collection (true/false)",
    )
    return parser


def main(argv: list[str] | None = None):
    argv = argv if argv is not None else sys.argv[1:]

    # Comandos especiais compatibles con script antiguo
    if argv and argv[0] == "infodb":
        DatabaseProcessor.print_db_info()
        return
    if argv and argv[0] == "process_all":
        proc = DatabaseProcessor()
        proc.process_all_themes()
        return

    # CLI normal
    parser = build_argparser()
    args = parser.parse_args(argv)

    overwrite_flag = args.overwrite.lower() == "true"

    proc = DatabaseProcessor(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    proc.process_theme(args.data_path, overwrite=overwrite_flag)


if __name__ == "__main__":
    main()