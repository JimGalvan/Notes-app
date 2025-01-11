from sqlalchemy.orm import Session
from models import Note, Tag
from typing import List, Optional
from datetime import datetime

class NoteOperations:
    def __init__(self, session: Session):
        self.session = session
    
    def create_note(self, title: str, content: str, color: str = "#2d2d2d",
                   position_x: float = None, position_y: float = None,
                   width: int = 300, height: int = 200,
                   text_size: int = 14) -> Note:
        note = Note(
            title=title,
            content=content,
            color=color,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            position_x=position_x,
            position_y=position_y,
            width=width,
            height=height,
            text_size=text_size
        )
        self.session.add(note)
        self.session.commit()
        return note
    
    def update_note(self, note_id: int, title: Optional[str] = None,
                   content: Optional[str] = None, color: Optional[str] = None,
                   position_x: Optional[float] = None,
                   position_y: Optional[float] = None,
                   width: Optional[int] = None,
                   height: Optional[int] = None,
                   text_size: Optional[int] = None) -> Note:
        note = self.session.query(Note).get(note_id)
        if note:
            if title is not None:
                note.title = title
            if content is not None:
                note.content = content
            if color is not None:
                note.color = color
            if position_x is not None:
                note.position_x = position_x
            if position_y is not None:
                note.position_y = position_y
            if width is not None:
                note.width = width
            if height is not None:
                note.height = height
            if text_size is not None:
                note.text_size = text_size
            note.updated_at = datetime.utcnow()
            self.session.commit()
        return note
    
    def delete_note(self, note_id: int) -> bool:
        note = self.session.query(Note).get(note_id)
        if note:
            self.session.delete(note)
            self.session.commit()
            return True
        return False
    
    def get_all_notes(self) -> List[Note]:
        return self.session.query(Note).order_by(Note.updated_at.desc()).all()
    
    def search_notes(self, query: str) -> List[Note]:
        search = f"%{query}%"
        return self.session.query(Note).filter(
            (Note.title.ilike(search)) | (Note.content.ilike(search))
        ).order_by(Note.updated_at.desc()).all()
    
    def add_tag(self, note_id: int, tag_name: str, color: str = "#e0e0e0") -> Optional[Tag]:
        note = self.session.query(Note).get(note_id)
        if not note:
            return None
            
        tag = self.session.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name, color=color)
            self.session.add(tag)
            
        note.tags.append(tag)
        self.session.commit()
        return tag
    
    def remove_tag(self, note_id: int, tag_name: str) -> bool:
        note = self.session.query(Note).get(note_id)
        if not note:
            return False
            
        tag = self.session.query(Tag).filter(Tag.name == tag_name).first()
        if tag and tag in note.tags:
            note.tags.remove(tag)
            self.session.commit()
            return True
        return False
    
    def get_tags(self) -> List[Tag]:
        return self.session.query(Tag).all() 