from app import app
from models import User

def inspect_user_table():
    print("User Table Schema:")
    for column in User.__table__.columns:
        print(f"  {column.name}: {column.type} (nullable: {column.nullable})")

if __name__ == "__main__":
    with app.app_context():
        inspect_user_table()
