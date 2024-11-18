import uuid
import os
from contextlib import asynccontextmanager
from typing import Annotated, Sequence

from fastapi import FastAPI, Depends
from fastapi.security import APIKeyHeader
from sqlmodel import Field, Session, SQLModel, create_engine, select
from starlette.exceptions import HTTPException

predefined_token = os.getenv("REST_API_KEY")

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)


class Task(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(bind=engine)


SessionDep = Annotated[Session, Depends(get_session)]


def initial_data():
    task_1 = Task(title="Task1", description="This is Task 1")
    task_2 = Task(title="Task2", description="This is Task 2")
    task_3 = Task(title="Task3", description="This is Task 3")

    with Session(engine) as session:
        session.add(task_1)
        session.add(task_2)
        session.add(task_3)

        session.commit()


def get_all_tasks(session: SessionDep) -> Sequence[Task]:
    return session.exec(select(Task)).all()


@asynccontextmanager
async def lifespan(current_app: FastAPI):
    create_db_and_tables()
    initial_data()
    yield


app = FastAPI(lifespan=lifespan)

api_key_header = APIKeyHeader(name="X-API-Key")



def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != predefined_token:
        raise HTTPException(status_code=401, detail="Invalid API Key")


@app.get("/tasks")
def read_root(session: SessionDep, api_key: str = Depends(get_api_key)) -> Sequence[Task]:
    return get_all_tasks(session)
