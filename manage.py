from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import app, db, models, app_sheduler
from app.models import User, Activity
from app.ground.helper import update_grounds_dataset
import coverage
import os
import forgery_py as faker
from random import randint
from sqlalchemy.exc import IntegrityError

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
    user = User.query.filter_by(email="example@bucketmail.com").first()
    if not user:
        user = User("example@bucketmail.com", "123456")
        user.save()


# Run the manager
if __name__ == '__main__':
    manager.run()
