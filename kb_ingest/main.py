"""CLI entrypoint for the knowledge ingestion project."""

from dotenv import load_dotenv
load_dotenv()

from kb_service.cli import main

if __name__ == "__main__":
    main()
