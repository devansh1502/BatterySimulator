from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
Session = sessionmaker()

def configure_database(conn_url: str = "sqlite:///octave.db"):
    engine = create_engine(conn_url, future=True)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine, future=True)
