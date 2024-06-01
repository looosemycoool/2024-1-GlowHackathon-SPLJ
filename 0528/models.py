from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./politician_db.db"
Base = declarative_base()

class Politician(Base):
    __tablename__ = "politicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    region = Column(String, index=True)
    promises = relationship("Promise", back_populates="politician", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")

    def total_fulfillment_rate(self):
        total = len(self.promises)
        if total == 0:
            return 0
        completed = sum(1 for promise in self.promises if promise.status == '이행 완료')
        return (completed / total) * 100

class Promise(Base):
    __tablename__ = "promises"

    id = Column(Integer, primary_key=True, index=True)
    politician_id = Column(Integer, ForeignKey("politicians.id"))
    description = Column(String, index=True)
    status = Column(String, default="확인 불가")
    politician = relationship("Politician", back_populates="promises")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    author_id = Column(Integer, ForeignKey("politicians.id"))
    author = relationship("Politician", back_populates="posts")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
