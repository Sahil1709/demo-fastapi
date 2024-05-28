from typing import Union, Annotated

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database import crud, models, schemas
from database.database import SessionLocal, engine
import datetime, os
from app.schedulers import scheduler
from app.queue import file_queue

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None

@app.on_event("startup")
async def startup_event():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...),  db: Session = Depends(get_db)):
    contents = await file.read()
    metadata = {
        "filename": file.filename,
        "content_type": file.content_type,
        "file_size": file.size,
        "file_headers": file.headers,
        "file_extension": file.filename.split(".")[-1],
        "file_size_kb": file.size / 1024,
        "contents": contents,
    }

    file_queue.put(metadata)
    
    return {"filename": file.filename, "status": "File added to upload queue"}

@app.get("/files")
def get_all_files(db: Session = Depends(get_db)):
    files = crud.get_all_files(db)
    return files

@app.get("/files/{file_id}")
def get_file(file_id: str, db: Session = Depends(get_db)):
    file = crud.get_file(db, file_id)
    if file:
        return file
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/files/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db)):
    file = crud.get_file(db, file_id)
    if file:
        file_path = file.path
        crud.delete_file(db, file_id)
        try:
            os.remove(file_path)
        except OSError:
            pass
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.delete("/files/")
def delete_multiple_files(files: list[str], db: Session = Depends(get_db)):
    response = []
    for file_id in files:
        file = crud.get_file(db, file_id)
        if file:
            file_path = file.path
            crud.delete_file(db, file_id)
            try:
                os.remove(file_path)
            except OSError:
                pass
            response.append({file_id: "File deleted successfully"})
        else:
            response.append({file_id: "File not found"})
    return response


# =============== USERS & ITEMS ===============

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items





# todo:
# - nnotate funcions, comments and docstrings, for tests and main 
