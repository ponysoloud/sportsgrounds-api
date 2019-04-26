from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import app, db, models, app_sheduler
from app.models import User, Bucket, BucketItem, ActivitiesEnum, Activity
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
def populate_activities():
    print('setup_activities')
    for a in ActivitiesEnum:
        activity = Activity(a.value, a.name, a.description)
        activity.save()
    
@manager.command
def update_grounds():
    print('update_grounds')
    update_grounds_dataset()

@manager.command
def dummy():
    # Create a user if they do not exist.
    user = User.query.filter_by(email="example@bucketmail.com").first()
    if not user:
        user = User("example@bucketmail.com", "123456")
        user.save()

    for i in range(100):
        # Add buckets to the database
        bucket = Bucket(faker.name.industry(), user.id)
        bucket.save()

    for buck in range(1000):
        # Add items to the bucket
        buckt = Bucket.query.filter_by(id=randint(1, Bucket.query.count() - 1)).first()
        item = BucketItem(faker.name.company_name(), faker.lorem_ipsum.word(), buckt.id)
        db.session.add(item)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


# Run the manager
if __name__ == '__main__':
    manager.run()
