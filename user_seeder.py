from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.models import User, UserRole
from faker import Faker
import random

app = Flask(__name__)
app.config.from_object('config.Config')
fake = Faker()
db = SQLAlchemy()
db.init_app(app)

def seed_users(n):
    # admin = User(
    #         name="Admin",
    #         email="admin@spil.id",
    #         role=UserRole.admin,
    #         approved=True
    #     )
    
    # admin.set_password("12345678")

    # db.session.add(admin)
    
    for _ in range(n):
        name = fake.name()
        email = fake.unique.email()
        password = "12345678"
        
        # Random role between 'user', 'admin', 'guest'
        role = random.choice([UserRole.user, UserRole.admin, UserRole.guest])

        # Randomly approve users (None or True)
        approved = random.choice([None, True])

        user = User(
            name=name,
            email=email,
            role=role,
            approved=approved
        )
        user.set_password(password)
    
        db.session.add(user)

    db.session.commit()
    print(f'{n} users added successfully!')

if __name__ == '__main__':
    with app.app_context():        
        seed_users(10)