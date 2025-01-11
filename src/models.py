from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

note_tags = Table(
    'note_tags',
    Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    color = Column(String(7), default='#ffffff')  # Hex color code
    is_pinned = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    position_x = Column(Integer, nullable=True)  # For sticky note positioning
    position_y = Column(Integer, nullable=True)  # For sticky note positioning
    width = Column(Integer, default=300)  # Default width
    height = Column(Integer, default=200)  # Default height
    text_size = Column(Integer, default=14)  # Default font size
    
    tags = relationship('Tag', secondary=note_tags, back_populates='notes')

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    color = Column(String(7), default='#e0e0e0')  # Hex color code
    
    notes = relationship('Note', secondary=note_tags, back_populates='tags') 