from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.user import Base
import os

def get_engine():
    db_path = os.getenv('DB_PATH', 'backend/db/app.db')
    return create_engine(f'sqlite:///{db_path}', echo=False)

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == '__main__':
    init_db()
    print('Database initialized.')
