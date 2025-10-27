"""CLI entrypoint for the knowledge ingestion project."""

from dotenv import load_dotenv
load_dotenv()

from app.cli import main

if __name__ == "__main__":
    main()
