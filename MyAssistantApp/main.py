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

# PersonalPassword
class Password(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str
    password: str

class Task(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str
    
# Notes
class Note(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    value: str

def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(bind=engine)


SessionDep = Annotated[Session, Depends(get_session)]


def initial_data():
    password_1 = Password(username="Alu1", password="password123")
    password_2 = Password(username="potol2", password="password456")
    task_1 = Task(title="Task1", description="This is Task 1")
    task_2 = Task(title="Task2", description="This is Task 2")
    task_3 = Task(title="Task3", description="This is Task 3")
    note_1 = Note(title="Note 1", value="Destination: Paris\nDates: 2023-06-01 to 2023-06-10\nBookings:\n- Flight on 2023-05-31, return on 2023-06-11\n- Hotel: City Center Hotel, booking ID: 987654321, Meeting Date: 2023-01-15\nAttendees: Alice, Bob, Charlie\nDiscussion:\n- Budget review\n- Project timelines update\n- New hiring proposals, Gmail: Alu1, password123\nBank Account: potol2, password456\nNetflix: user3, pass789")
    note_2 = Note(title="Note 2", value="Alu1: password123, potol2: password456")

    with Session(engine) as session:
        session.add_all([password_1, password_2, task_1, task_2, task_3, note_1, note_2])
        session.commit()


def get_all_tasks(session: SessionDep) -> Sequence[Task]:
    return session.exec(select(Task)).all()


def get_all_passwords(session: SessionDep) -> Sequence[Password]:
    return session.exec(select(Password)).all()

def get_all_notes(session: SessionDep) -> Sequence[Note]:
    return session.exec(select(Note)).all()

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

@app.get("/passwords")
def read_root(session: SessionDep, api_key: str = Depends(get_api_key)) -> Sequence[Password]:
    return get_all_passwords(session)

@app.get("/tasks")
def read_root(session: SessionDep, api_key: str = Depends(get_api_key)) -> Sequence[Task]:
    return get_all_tasks(session)

@app.get("/notes")
def read_root(session: SessionDep, api_key: str = Depends(get_api_key)) -> Sequence[Note]:
    return get_all_notes(session)

