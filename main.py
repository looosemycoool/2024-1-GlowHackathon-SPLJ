from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import Base, Politician, Promise, SessionLocal, engine
from pydantic import BaseModel

app = FastAPI()

# Pydantic 모델
class PromiseCreate(BaseModel):
    description: str
    fulfillment_rate: float

class PromiseModel(PromiseCreate):
    id: int
    politician_id: int

    class Config:
        from_attributes = True

class PoliticianCreate(BaseModel):
    name: str
    region: str

class PoliticianModel(PoliticianCreate):
    id: int
    promises: List[PromiseModel] = []

    class Config:
        from_attributes = True

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
