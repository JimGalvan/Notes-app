from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base as ModelsBase
from note_operations import Base as OperationsBase

class Database:
    def __init__(self):
        self.engine = create_engine('sqlite:///notes.db')
        
        # Create all tables
        ModelsBase.metadata.create_all(self.engine)
        OperationsBase.metadata.create_all(self.engine)
        
        # Create session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def get_session(self):
        return self.session
    
    def close(self):
        self.session.close() 