from sqlalchemy import Column, Integer, String, Float, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./politician_db.db"
Base = declarative_base()

class Politician(Base):
    __tablename__ = "politicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    region = Column(String, index=True)
    promises = relationship("Promise", back_populates="politician")

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
    status = Column(String, default = "확인 불가")
    politician = relationship("Politician", back_populates="promises")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)






