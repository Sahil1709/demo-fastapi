# fastapi imports
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile
from typing import Union, Annotated

# database imports
from sqlalchemy.orm import Session
from database import crud, models, schemas
from database.database import SessionLocal, engine
from pydantic import BaseModel

# apscheduler imports
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.schedulers import scheduler
from app.schedulers import startup_event
from app.schedulers import shutdown_event

# other imports
import json
import datetime, os
from app.queue import file_queue

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_event_handler('startup', startup_event)
app.add_event_handler('shutdown', shutdown_event)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CORS
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

# test item class
class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


# root endpoint
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Retrieve an item by its ID
@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    """
    Retrieve an item by its ID.

    Parameters:
        - item_id (int): The ID of the item to retrieve.
        - q (Union[str, None], optional): An optional query parameter.

    Returns:
        dict: A json response containing the item ID and the query parameter (if provided).
    """
    return {"item_id": item_id, "q": q}

# Update an item by its ID
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    """
    Update an item by its ID.

    Parameters:
        - item_id (int): The ID of the item to update.
        - item (Item): The updated item data.

    Returns:
        dict: A json response containing the updated item name and ID.
    """
    return {"item_name": item.name, "item_id": item_id}

# Upload a file
@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Uploads a file to the server.

    Parameters:
    - file: The file to be uploaded (required).
    - db: The database session (optional).

    Returns:
    A json response containing the filename and status of the upload.

    Raises:
    - HTTPException: If the file upload fails.
    """
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

# Retrieve all files
@app.get("/files")
def get_all_files(db: Session = Depends(get_db)):
    """
    Retrieve all files from the database.

    Parameters:
        - db (Session): The database session.

    Returns:
        list: A list of files.
    """
    files = crud.get_all_files(db)
    return files

# Retrieve a file by its ID
@app.get("/files/{file_id}")
def get_file(file_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a file by its ID.

    Parameters:
        - file_id (str): The ID of the file to retrieve.
        - db (Session): The database session.

    Returns:
        dict: A json response containing the file data.

    Raises:
        HTTPException: If the file is not found.
    """
    file = crud.get_file(db, file_id)
    if file:
        return file
    else:
        raise HTTPException(status_code=404, detail="File not found")

# Delete a file by its ID
@app.delete("/files/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db)):
    """
    Delete a file by its ID.

    Parameters:
        - file_id (str): The ID of the file to delete.
        - db (Session): The database session.

    Returns:
        dict: A json response indicating the success of the deletion.

    Raises:
        HTTPException: If the file is not found.
    """
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

# Delete multiple files
@app.delete("/files/")
def delete_multiple_files(files: list[str], db: Session = Depends(get_db)):
    """
    Delete multiple files.

    Parameters:
        - files (list[str]): A list of file IDs to delete.
        - db (Session): The database session.

    Returns:
        list: A list of json responses indicating the success of each deletion.
    """
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

# Create a new user
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.

    Parameters:
        - user (schemas.UserCreate): The user data.
        - db (Session): The database session.

    Returns:
        dict: A json response containing the created user data.

    Raises:
        HTTPException: If the email is already registered.
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

# Retrieve a list of users
@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of users.

    Parameters:
        - skip (int): The number of users to skip.
        - limit (int): The maximum number of users to retrieve.
        - db (Session): The database session.

    Returns:
        list: A list of users.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Retrieve a user by its ID
@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a user by its ID.

    Parameters:
        - user_id (int): The ID of the user to retrieve.
        - db (Session): The database session.

    Returns:
        dict: A json response containing the user data.

    Raises:
        HTTPException: If the user is not found.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Create an item for a user
@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    """
    Create an item for a user.

    Parameters:
        - user_id (int): The ID of the user.
        - item (schemas.ItemCreate): The item data.
        - db (Session): The database session.

    Returns:
        dict: A json response containing the created item data.

    Raises:
        HTTPException: If the user is not found.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_user_item(db=db, item=item, user_id=user_id)

# Retrieve a list of items
@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of items.

    Parameters:
        - skip (int): The number of items to skip.
        - limit (int): The maximum number of items to retrieve.
        - db (Session): The database session.

    Returns:
        list: A list of items.
    """
    items = crud.get_items(db, skip=skip, limit=limit)
    return items
