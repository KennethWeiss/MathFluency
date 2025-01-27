from app import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, JSON, DateTime
from typing import Optional, Dict, Any
from models.user import User
from datetime import datetime

class OAuth(db.Model):
    __tablename__ = 'oauth'

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    token: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Foreign key to user
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    user: Mapped["User"] = relationship()

    def __repr__(self):
        return f'<OAuth {self.provider}>'
