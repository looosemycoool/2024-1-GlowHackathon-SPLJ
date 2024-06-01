import os
import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from models import Base, engine, Politician, Promise, Post, SessionLocal

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

if not os.path.exists("templates"):
    os.makedirs("templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class PostCreate(BaseModel):
    title: str
    content: str
    author_id: int

class PostModel(PostCreate):
    id: int

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def validate_params(name: Optional[str] = None, region: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    if not name and not region:
        raise HTTPException(status_code=400, detail="이름이나 지역 중 하나는 반드시 제공되어야 합니다.")
    return name, region

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"템플릿 렌더링 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류")

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
def create_promise_for_politician(politician_id: int, promise: PromiseCreate, db: Session = Depends(get_db)):
    db_promise = Promise(**promise.dict(), politician_id=politician_id)
    db.add(db_promise)
    db.commit()
    db.refresh(db_promise)
    return db_promise

@app.get("/politicians/search/", response_model=List[PoliticianModel])
def search_politicians(params: Tuple[Optional[str], Optional[str]] = Depends(validate_params), db: Session = Depends(get_db)):
    name, region = params
    query = db.query(Politician)
    
    if name:
        query = query.filter(Politician.name.ilike(f"%{name}%"))
    
    if region:
        query = query.filter(Politician.region.ilike(f"%{region}%"))
    
    politicians = query.all()
    
    for politician in politicians:
        politician.calculate_fulfillment_rate = politician.total_fulfillment_rate()
    
    return politicians

@app.get("/promises/", response_class=HTMLResponse)
async def read_promises(request: Request, db: Session = Depends(get_db)):
    promises = db.query(Promise).all()
    return templates.TemplateResponse("promises.html", {"request": request, "promises": promises})

@app.get("/promises/{politician_id}", response_class=HTMLResponse)
async def get_politician_promises(politician_id: int, request: Request, db: Session = Depends(get_db)):
    politician = db.query(Politician).filter(Politician.id == politician_id).first()
    if not politician:
        raise HTTPException(status_code=404, detail="정치인을 찾을 수 없습니다")
    return templates.TemplateResponse("promises.html", {
        "request": request,
        "name": politician.name,
        "region": politician.region,
        "id": politician.id,
        "promises": politician.promises
    })

@app.post("/posts/", response_model=PostModel)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    db_post = Post(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/posts/", response_model=List[PostModel])
def read_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    posts = db.query(Post).offset(skip).limit(limit).all()
    return posts

@app.get("/posts/{post_id}", response_model=PostModel)
def read_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다")
    return post

@app.put("/posts/{post_id}", response_model=PostModel)
def update_post(post_id: int, post: PostCreate, db: Session = Depends(get_db)):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다")
    
    for key, value in post.dict().items():
        setattr(db_post, key, value)
    
    db.commit()
    db.refresh(db_post)
    return db_post

@app.delete("/posts/{post_id}", response_model=PostModel)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다")
    
    db.delete(db_post)
    db.commit()
    return db_post

@app.get("/posts/", response_class=HTMLResponse)
async def read_posts_html(request: Request, db: Session = Depends(get_db)):
    posts = db.query(Post).all()
    return templates.TemplateResponse("posts.html", {"request": request, "posts": posts})

# 데이터베이스 초기 데이터 추가
from sqlalchemy.orm import sessionmaker
from models import engine, Politician, Promise
Session = sessionmaker(bind=engine)
session = Session()

politician1 = Politician(name="홍준표", region="대구시장")
session.add(politician1)

politician2 = Politician(name="우재준", region="대구북구갑")
session.add(politician2)

session.commit()

promise1 = Promise(description="교통 개선 프로젝트", status="이행 완료", politician_id=politician1.id)
session.add(promise1)

promise2 = Promise(description="환경 보호 캠페인", status="진행 중", politician_id=politician1.id)
session.add(promise2)

promise3 = Promise(description="교육 지원 확대", status="이행 완료", politician_id=politician2.id)
session.add(promise3)

session.commit()
