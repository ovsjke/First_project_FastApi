import uvicorn

from api import create_app
from database.database_config import engine
from database.models import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def run_api() -> None:
    uvicorn.run(create_app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    init_db()
    run_api()