from app import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, JSON
from typing import Optional, Dict, Any
from models.user import User

class OAuth(db.Model):
    __tablename__ = 'flask_dance_oauth'  # Keep the existing table name to avoid migration issues

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50))
    provider_user_id: Mapped[str] = mapped_column(String(256))
    token: Mapped[Dict[str, Any]] = mapped_column(JSON)
    
    # Foreign key to user
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    user: Mapped["User"] = relationship()

    def __repr__(self):
        return f'<OAuth {self.provider}:{self.provider_user_id}>'
