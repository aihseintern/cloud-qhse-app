# guide_bot/models.py
from app import db
from app.models import User

# Document: id, title, file, created_at, updated_at
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), index=True)
    dir = db.Column(db.String(120), index=True)
    file = db.Column(db.LargeBinary)
    created_at = db.Column(db.DateTime, index=True, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, index=True, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    allowed_roles = db.Column(db.String(100), default='manager')  # Comma-separated list of roles

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'dir': self.dir,
            'file': self.file,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'allowed_roles': self.allowed_roles
        }

    def __repr__(self):
        return f'<Document {self.title}>'

    def is_accessible_by(self, user):
        if user.is_manager():
            return True
        return user.role in self.allowed_roles.split(',')
    
class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('chat_rooms', lazy=True))
    name = db.Column(db.String(120), index=True)
    created_at = db.Column(db.DateTime, index=True, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, index=True, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def __repr__(self):
        return f'<ChatRoom {self.name}>'

