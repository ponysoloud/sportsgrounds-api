import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

from apscheduler.schedulers.background import BackgroundScheduler

# Initialize application
app = Flask(__name__, static_folder=None)

# Enabling cors
CORS(app)

# app configuration
app_configuration = os.getenv('APP_CONFIGURATION', 'app.config.DevelopmentConfig')
app.config.from_object(app_configuration)

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Initialize Flask Sql Alchemy
db = SQLAlchemy(app)

# Initialize Sheduler
app_sheduler = BackgroundScheduler(timezone='utc')
app_sheduler.start()

# Import the application views
from app import views

# Register blue prints
from app.auth.views import auth

app.register_blueprint(auth)

from app.ground.views import ground

app.register_blueprint(ground)

from app.activity.views import activity

app.register_blueprint(activity)

from app.bucket.views import bucket

app.register_blueprint(bucket)

from app.bucketitems.views import bucketitems

app.register_blueprint(bucketitems)

from app.docs.views import docs

app.register_blueprint(docs)