from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

engine = None


def get_engine(test=False):
    if test:
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        SQLModel.metadata.create_all(engine)
    else:
        engine = create_engine(url="sqlite:///microservice.db")
    return engine


def get_session():
    global engine
    if engine is None:
        engine = get_engine(test=False)
    with Session(engine) as session:
        yield session


def get_test_session():
    global engine
    if engine is None:
        engine = get_engine(test=True)
    with Session(engine) as session:
        yield session


def create_tables():
    global engine
    if engine is None:
        engine = get_engine(test=False)
    SQLModel.metadata.create_all(engine)
