import logging
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db.base import Base
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created")


def create_initial_data(db: Session) -> None:
    # Check if we already have connections
    connection = crud.db_connection.get_by_name(db, name="Sample Database")
    if not connection:
        connection_in = schemas.DBConnectionCreate(
            name="Sample Database",
            db_type="mysql",
            host="localhost",
            port=3306,
            username="root",
            password="mysql",
            database_name="chat_db"
        )
        connection = crud.db_connection.create(db=db, obj_in=connection_in)
        logger.info(f"Created sample connection: {connection.name}")


if __name__ == "__main__":
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        init_db(db)
        create_initial_data(db)
    finally:
        db.close()
