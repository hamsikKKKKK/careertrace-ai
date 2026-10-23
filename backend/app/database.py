from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from .models import Base

def database(url=None):
    if not url:
        folder = Path(__file__).resolve().parent.parent / 'data'
        folder.mkdir(exist_ok=True)
        url = f"sqlite:///{folder / 'careertrace.db'}"
    engine = create_engine(url, connect_args={'check_same_thread': False})
    @event.listens_for(engine, 'connect')
    def sqlite_config(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    return engine, sessionmaker(engine, expire_on_commit=False)
