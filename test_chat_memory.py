from db import SessionLocal
from chat_manager import save_message

db = SessionLocal()

save_message(
    session=db,
    user_id=1,
    role="user",
    content="Hello"
)

print("Message saved successfully")