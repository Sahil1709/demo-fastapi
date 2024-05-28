# apscheduler imports
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# database imports
from database.database import SessionLocal
from database import crud

# other imports
import datetime
import os
from app.queue import file_queue

scheduler = AsyncIOScheduler()

# Function to run at startup
async def startup_event():
    scheduler.start()

# Function to run at shutdown
async def shutdown_event():
    scheduler.shutdown()

# Function to delete files older than 20 minutes
def delete_old_files():
    print("Searching for old files........")
    with SessionLocal() as db:
        files = crud.get_all_files(db)
        now = datetime.datetime.now()
        for file in files:
            file_timestamp_str = file.path.split("/")[-1].split("_")[0]
            file_timestamp = datetime.datetime.strptime(file_timestamp_str, "%Y%m%d-%H%M%S")
            file_age = (now - file_timestamp).total_seconds()
            if file_age > 20 * 60:  # 20 minutes
                try:
                    os.remove(file.path)
                except FileNotFoundError:
                    pass
                crud.delete_file(db, file.id)
                print(f"Deleted file {file.filename} (ID: {file.id})") 

# Function to upload files from the queue
async def upload_files_from_queue():
    print("Uploading files from the queue.......")
    with SessionLocal() as db:
        while not file_queue.empty():
            metadata = file_queue.get()
            current_date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            file_path = f'files/{current_date}_{metadata["filename"]}'

            with open(file_path, "wb") as f:
                f.write(metadata["contents"])

            created_file = crud.create_file(db, metadata["filename"], file_path)
            metadata["file_id"] = created_file.id

            print(f"Uploaded file {metadata['filename']} (ID: {metadata['file_id']})")

# Function to delete excess users
async def delete_excess_users():
    print("Deleting excess users.......")
    with SessionLocal() as db:
        users = crud.get_users(db)
        if len(users) > 10:
            users_to_delete = users[10:]
            for user in users_to_delete:
                crud.delete_user(db, user.id)

# Function to delete excess items
async def delete_excess_items():
    print("Deleting excess items.......")
    with SessionLocal() as db:
        items = crud.get_items(db)
        if len(items) > 10:
            items_to_delete = items[10:]
            for item in items_to_delete:
                crud.delete_item(db, item.id)

# Scheduler job that runs delete_old_files every 5 minutes
scheduler.add_job(
    delete_old_files,
    trigger=IntervalTrigger(minutes=5),
    id="delete_old_files",
    name="Delete old files every 5 minutes",
    replace_existing=True,
)

# Scheduler job that runs upload_files_from_queue every 4 minutes
scheduler.add_job(
    upload_files_from_queue,
    trigger=IntervalTrigger(minutes=4),
    id="upload_files_from_queue",
    name="Upload Files from the queue every 4 minute",
)

# Scheduler job that runs delete_excess_users every 10 minutes
scheduler.add_job(
    delete_excess_users,
    trigger=IntervalTrigger(minutes=10),
    id="delete_excess_users",
    name="Delete excess users every 10 minutes",
    replace_existing=True,
)

# Scheduler job that runs delete_excess_items every 10 minutes
scheduler.add_job(
    delete_excess_items,
    trigger=IntervalTrigger(minutes=10),
    id="delete_excess_items",
    name="Delete excess items every 10 minutes",
    replace_existing=True,
)