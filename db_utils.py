import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String) # Hashed

class EmailCredential(Base):
    __tablename__ = "email_credentials"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    imap_server = Column(String)
    email_address = Column(String)
    app_password = Column(String)

class ScanHistory(Base):
    __tablename__ = "scan_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String) # 'Email', 'Manual', 'Bulk'
    content_preview = Column(Text)
    prediction = Column(Integer) # 1 for Spam, 0 for Ham
    phishing_risk = Column(Integer, default=0) # 0 to 100 score

# Create tables
Base.metadata.create_all(bind=engine)

def load_all_users():
    db = SessionLocal()
    users = db.query(User).all()
    credentials = {"usernames": {}}
    for user in users:
        credentials["usernames"][user.username] = {
            "email": user.email,
            "name": user.name,
            "password": user.password
        }
    db.close()
    return credentials

def add_user_to_db(username, name, email, hashed_password):
    db = SessionLocal()
    if not db.query(User).filter(User.username == username).first():
        new_user = User(
            username=username,
            name=name,
            email=email,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.close()
        return True
    db.close()
    return False

def save_scan_result(username, source, content, prediction, phishing_risk=0):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user:
        scan = ScanHistory(
            user_id=user.id,
            source=source,
            content_preview=content[:200],
            prediction=int(prediction),
            phishing_risk=int(phishing_risk)
        )
        db.add(scan)
        db.commit()
    db.close()

def get_user_analytics(username):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    stats = {}
    if user:
        scans = db.query(ScanHistory).filter(ScanHistory.user_id == user.id).all()
        stats['total_scans'] = len(scans)
        stats['spam_count'] = len([s for s in scans if s.prediction == 1])
        stats['ham_count'] = stats['total_scans'] - stats['spam_count']
        stats['phishing_alerts'] = len([s for s in scans if s.phishing_risk > 50])
        
        # Recent activity for charts
        stats['history'] = [
            {"date": s.timestamp.strftime("%Y-%m-%d %H:%M"), "pred": s.prediction} 
            for s in scans[-50:]
        ]
    db.close()
    return stats

def save_email_config(username, imap_server, email_address, app_password):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user:
        config = db.query(EmailCredential).filter(EmailCredential.user_id == user.id).first()
        if config:
            config.imap_server = imap_server
            config.email_address = email_address
            config.app_password = app_password
        else:
            config = EmailCredential(
                user_id=user.id,
                imap_server=imap_server,
                email_address=email_address,
                app_password=app_password
            )
            db.add(config)
        db.commit()
    db.close()

def load_email_config(username):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    config_data = None
    if user:
        config = db.query(EmailCredential).filter(EmailCredential.user_id == user.id).first()
        if config:
            config_data = {
                "imap_server": config.imap_server,
                "email_address": config.email_address,
                "app_password": config.app_password
            }
    db.close()
    return config_data

def init_db():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        admin = User(
            username="admin",
            name="Admin User",
            email="admin@example.com",
            password="$2b$12$4J/YtxM5LfjyvJfwPEMoyOCUbJpYHEdhM2xKmYhNAJxGyGbfgTcqC"
        )
        db.add(admin)
        db.commit()
    db.close()

init_db()
