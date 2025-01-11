from sqlalchemy.orm import Session
from models import Note, Tag
from typing import List, Optional
from datetime import datetime

class NoteOperations:
    def __init__(self, session: Session):
        self.session = session
    
    def create_note(self, title: str, content: str, color: str = "#ffffff") -> Note:
        note = Note(
            title=title,
            content=content,
            color=color,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(note)
        self.session.commit()
        return note
    
    def update_note(self, note_id: int, title: str, content: str, color: Optional[str] = None) -> Note:
        note = self.session.query(Note).get(note_id)
        if note:
            note.title = title
            note.content = content
            if color:
                note.color = color
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