
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=True)
    role = Column(String, default='User')  # Admin/User
    registration_date = Column(DateTime, default=datetime.now)

    archives = relationship('Archive', back_populates='user')

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}', role='{self.role}')>"

class Archive(Base):
    __tablename__ = 'archive'
    archive_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    hijri_month = Column(String)
    week_number = Column(String) # الأول، الثاني، الثالث، الرابع
    activity_type = Column(String)
    content_type = Column(String) # صور مع الخبر, فيديو, صورة مع الخبر, etc.
    news_text = Column(Text)
    file_telegram_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

    user = relationship('User', back_populates='archives')

    def __repr__(self):
        return f"<Archive(archive_id={self.archive_id}, hijri_month='{self.hijri_month}', activity_type='{self.activity_type}')>"

DATABASE_URL = "sqlite:///./archive_bot.db"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to initialize the database and add a default admin if not exists
def init_db(admin_user_id: int, admin_username: str):
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.user_id == admin_user_id).first()
        if not existing_admin:
            new_admin = User(user_id=admin_user_id, username=admin_username, role='Admin')
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            print(f"Default admin {admin_username} ({admin_user_id}) added.")
        else:
            print(f"Admin {admin_username} ({admin_user_id}) already exists.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
