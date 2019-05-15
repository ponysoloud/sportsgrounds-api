import coverage
import os
import forgery_py as faker
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import app, db, models, app_sheduler
from app.models import User, Activity
from app.ground.helper import update_grounds_dataset
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# Initializing the manager
manager = Manager(app)

# Initialize Flask Migrate
migrate = Migrate(app, db)

# Add the flask migrate
manager.add_command('db', MigrateCommand)
    
@manager.command
def load_grounds():
    update_grounds_dataset()

@manager.command
def dummy():
    # Create a user if they do not exist.
    user1 = User.query.filter_by(email="user1@test.com").first()
    if not user1:
        user1 = User("user1@test.com", "password", "Александр", "Пономарев", datetime.datetime(1997, 4, 30))
        user1.save()

    user2 = User.query.filter_by(email="user2@test.com").first()
    if not user2:
        user2 = User("user2@test.com", "password", "Николай", "Курчатов", datetime.datetime(1997, 4, 15))
        user2.save()

    user3 = User.query.filter_by(email="user3@test.com").first()
    if not user3:
        user3 = User("user3@test.com", "password", "Матвей", "Кравцов", datetime.datetime(1997, 7, 6))
        user3.save()

    user4 = User.query.filter_by(email="user4@test.com").first()
    if not user4:
        user4 = User("user4@test.com", "password", "Дмитрий", "Жаров", datetime.datetime(1996, 12, 15))
        user4.save()    

    user5 = User.query.filter_by(email="user5@test.com").first()
    if not user5:
        user5 = User("user5@test.com", "password", "Андрей", "Шумилкин", datetime.datetime(1997, 9, 13))
        user5.save()


# Run the manager
if __name__ == '__main__':
    manager.run()
