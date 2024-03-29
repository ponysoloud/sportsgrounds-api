import os
import boto3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from flask_cors import CORS

from apscheduler.schedulers.background import BackgroundScheduler

# Initialize application
app = Flask(__name__, static_folder=None)

# Enabling cors
CORS(app)

# App configuration
app_configuration = os.getenv('APP_CONFIGURATION', 'app.config.DevelopmentConfig')
app.config.from_object(app_configuration)

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Initialize Flask Sql Alchemy
db = SQLAlchemy(app)

# Initialize SocketIO
sockets = SocketIO(app)

# Initialize S3 Storage
s3 = boto3.client(
   "s3",
   aws_access_key_id=os.getenv('BUCKETEER_AWS_ACCESS_KEY_ID'),
   aws_secret_access_key=os.getenv('BUCKETEER_AWS_SECRET_ACCESS_KEY')
)

# Initialize Sheduler
app_sheduler = BackgroundScheduler(timezone='utc')
app_sheduler.start()

# Import the application views
from app import views

# Register blue prints
from app.auth.views import auth

app.register_blueprint(auth)

from app.user.views import user

app.register_blueprint(user)

from app.ground.views import ground

app.register_blueprint(ground)

from app.activity.views import activity

app.register_blueprint(activity)

from app.event.views import event

app.register_blueprint(event)

from app.team.views import team

app.register_blueprint(team)

from app.uploads.views import uploads

app.register_blueprint(uploads)

from app.docs.views import docs

app.register_blueprint(docs)