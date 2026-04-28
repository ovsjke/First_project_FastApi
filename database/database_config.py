from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# создание базы данных

engine = create_engine("sqlite:////data/sql_app.db")
engine.connect()
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """
    Генератор сессий
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
