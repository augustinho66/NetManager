from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    projects = db.relationship('Project', backref='owner', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    map_filename = db.Column(db.String(300))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    devices = db.relationship('Device', backref='project', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'map_filename': self.map_filename,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'devices': [d.to_dict() for d in self.devices]
        }


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    device_type = db.Column(db.String(50), default='router')
    x = db.Column(db.Float, nullable=False, default=0.0)
    y = db.Column(db.Float, nullable=False, default=0.0)
    ip = db.Column(db.String(50))
    name = db.Column(db.String(100))
    dns = db.Column(db.String(100))
    gateway = db.Column(db.String(50))
    mac = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'device_type': self.device_type,
            'x': self.x,
            'y': self.y,
            'ip': self.ip,
            'name': self.name,
            'dns': self.dns,
            'gateway': self.gateway,
            'mac': self.mac,
            'notes': self.notes
        }

