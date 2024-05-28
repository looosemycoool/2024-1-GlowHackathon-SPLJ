from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from models import Base, Politician, Promise, SessionLocal, engine

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

# 기존 FastAPI 앱 생성 코드
app = FastAPI()

# CORS 미들웨어 추가
origins = [
    "http://localhost:3000",  # Next.js 기본 포트
    "https://politician_promise.com",  # 배포시 사용할 도메인
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Pydantic 모델
class PromiseCreate(BaseModel):
    description: str
    status: str

class PromiseModel(PromiseCreate):
    id: int
    politician_id: int

    class Config:
        orm_mode = True

class PoliticianCreate(BaseModel):
    name: str
    region: str

class PoliticianModel(PoliticianCreate):
    id: int
    promises: List[PromiseModel] = []
    calculate_fulfillment_rate: Optional[float] = None

    class Config:
        orm_mode = True

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.post("/politicians/", response_model=PoliticianModel)
def create_politician(politician: PoliticianCreate, db: Session = Depends(get_db)):
    db_politician = Politician(**politician.dict())
    db.add(db_politician)
    db.commit()
    db.refresh(db_politician)
    return db_politician

@app.get("/politicians/", response_model=List[PoliticianModel])
def read_politicians(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    politicians = db.query(Politician).offset(skip).limit(limit).all()
    for politician in politicians:
        politician.calculate_fulfillment_rate = politician.total_fulfillment_rate()
    return politicians

@app.post("/politicians/{politician_id}/promises/", response_model=PromiseModel)
def create_promise_for_politician(
    politician_id: int, promise: PromiseCreate, db: Session = Depends(get_db)
):
    db_promise = Promise(**promise.dict(), politician_id=politician_id)
    db.add(db_promise)
    db.commit()
    db.refresh(db_promise)
    return db_promise

# 데이터베이스 초기 데이터 추가
from sqlalchemy.orm import sessionmaker
from models import engine, Politician, Promise

Session = sessionmaker(bind=engine)
session = Session()

politician1 = Politician(name="홍길동", region="서울")
session.add(politician1)

politician2 = Politician(name="김철수", region="부산")
session.add(politician2)

session.commit()

promise1 = Promise(description="교통 개선 프로젝트", status="이행 완료", politician_id=politician1.id)
session.add(promise1)

promise2 = Promise(description="환경 보호 캠페인", status="진행 중", politician_id=politician1.id)
session.add(promise2)

promise3 = Promise(description="교육 지원 확대", status="이행 완료", politician_id=politician2.id)
session.add(promise3)

session.commit()
session.close()