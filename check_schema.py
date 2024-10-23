from app import app
from models import User, Casino, Account

def inspect_table(table):
    print(f"Table: {table.__tablename__}")
    for column in table.__table__.columns:
        print(f"  {column.name}: {column.type} (nullable: {column.nullable})")
    print()

with app.app_context():
    inspect_table(User)
    inspect_table(Casino)
    inspect_table(Account)

if __name__ == "__main__":
    with app.app_context():
        inspect_table(User)
        inspect_table(Casino)
        inspect_table(Account)
