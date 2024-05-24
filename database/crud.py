from sqlalchemy.orm import Session

from . import models, schemas
import bcrypt

# =========== USER & ITEMS ===========

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(bytes(user.password, "utf-8"), salt)
    db_user = models.User(email=user.email, hashed_password=hashed_password, salt=salt)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# =========== FILES ===========

def create_file(db: Session, filename: str, path: str):
    db_file = models.File(filename=filename, path=path)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_all_files(db: Session):
    return db.query(models.File).all()

def get_file(db: Session, file_id: str):
    return db.query(models.File).filter(models.File.id == file_id).first()

def delete_file(db: Session, file_id: str):
    db.query(models.File).filter(models.File.id == file_id).delete()
    db.commit()
    return True