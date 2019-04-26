from app import app, db, bcrypt
import datetime
import jwt

from enum import Enum

class User(db.Model):
    """
    Table schema
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    buckets = db.relationship('Bucket', backref='bucket', lazy='dynamic')

    def __init__(self, email, password):
        self.email = email
        self.password = bcrypt.generate_password_hash(password, app.config.get('BCRYPT_LOG_ROUNDS')) \
            .decode('utf-8')
        self.registered_on = datetime.datetime.now()

    def save(self):
        """
        Persist the user in the database
        :param user:
        :return:
        """
        db.session.add(self)
        db.session.commit()
        return self.encode_auth_token(self.id)

    def encode_auth_token(self, user_id):
        """
        Encode the Auth token
        :param user_id: User's Id
        :return:
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=app.config.get('AUTH_TOKEN_EXPIRY_DAYS'),
                                                                       seconds=app.config.get(
                                                                           'AUTH_TOKEN_EXPIRY_SECONDS')),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(token):
        """
        Decoding the token to get the payload and then return the user Id in 'sub'
        :param token: Auth Token
        :return:
        """
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
            is_token_blacklisted = BlackListToken.check_blacklist(token)
            if is_token_blacklisted:
                return 'Token was Blacklisted, Please login In'
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired, Please sign in again'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please sign in again'

    @staticmethod
    def get_by_id(user_id):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return User.query.filter_by(id=user_id).first()

    @staticmethod
    def get_by_email(email):
        """
        Check a user by their email address
        :param email:
        :return:
        """
        return User.query.filter_by(email=email).first()

    def reset_password(self, new_password):
        """
        Update/reset the user password.
        :param new_password: New User Password
        :return:
        """
        self.password = bcrypt.generate_password_hash(new_password, app.config.get('BCRYPT_LOG_ROUNDS')) \
            .decode('utf-8')
        db.session.commit()


class BlackListToken(db.Model):
    """
    Table to store blacklisted/invalid auth tokens
    """
    __tablename__ = 'blacklist_token'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.datetime.now()

    def blacklist(self):
        """
        Persist Blacklisted token in the database
        :return:
        """
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def check_blacklist(token):
        """
        Check to find out whether a token has already been blacklisted.
        :param token: Authorization token
        :return:
        """
        response = BlackListToken.query.filter_by(token=token).first()
        if response:
            return True
        return False


class Bucket(db.Model):
    """
    Class to represent the BucketList model
    """
    __tablename__ = 'buckets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    create_at = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)
    items = db.relationship('BucketItem', backref='item', lazy='dynamic')

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id
        self.create_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        """
        Persist a bucket in the database
        :return:
        """
        db.session.add(self)
        db.session.commit()

    def update(self, name):
        """
        Update the name of the Bucket
        :param name:
        :return:
        """
        self.name = name
        db.session.commit()

    def delete(self):
        """
        Delete a Bucket from the database
        :return:
        """
        db.session.delete(self)
        db.session.commit()

    def json(self):
        """
        Json representation of the bucket model.
        :return:
        """
        return {
            'id': self.id,
            'name': self.name,
            'createdAt': self.create_at.isoformat(),
            'modifiedAt': self.modified_at.isoformat()
        }


class BucketItem(db.Model):
    """
    BucketItem model class
    """
    __tablename__ = 'bucketitems'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    bucket_id = db.Column(db.Integer, db.ForeignKey('buckets.id'))
    create_at = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, name, description, bucket_id):
        self.name = name
        self.description = description
        self.bucket_id = bucket_id
        self.create_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        """
        Persist Item into the database
        :return:
        """
        db.session.add(self)
        db.session.commit()

    def update(self, name, description=None):
        """
        Update the records in the item
        :param name: Name
        :param description: Description
        :return:
        """
        self.name = name
        if description is not None:
            self.description = description
        db.session.commit()

    def delete(self):
        """
        Delete an item
        :return:
        """
        db.session.delete(self)
        db.session.commit()

    def json(self):
        """
        Json representation of the model
        :return:
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'bucketId': self.bucket_id,
            'createdAt': self.create_at.isoformat(),
            'modifiedAt': self.modified_at.isoformat()
        }

grounds_to_activities_table = db.Table('groundsactivities', db.Model.metadata,
    db.Column('activity_id', db.Integer, db.ForeignKey('activities.id'), primary_key=True),
    db.Column('ground_id', db.Integer, db.ForeignKey('grounds.id'), primary_key=True)
)

class Ground(db.Model):
    """
    Class to represent the Ground model
    """
    __tablename__ = 'grounds'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_id = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    website = db.Column(db.String(255), nullable=True)

    hasMusic = db.Column(db.Boolean, default=False, nullable=False)
    hasWifi = db.Column(db.Boolean, default=False, nullable=False)
    hasToilet = db.Column(db.Boolean, default=False, nullable=False)
    hasEatery = db.Column(db.Boolean, default=False, nullable=False)
    hasDressingRoom = db.Column(db.Boolean, default=False, nullable=False)
    hasLighting = db.Column(db.Boolean, default=False, nullable=False)
    paid = db.Column(db.Boolean, default=False, nullable=False)

    latitude = db.Column(db.Float(), nullable=False)
    longitude = db.Column(db.Float(), nullable=False)
    
    #user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    create_at = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)

    activities = db.relationship('Activity', secondary=grounds_to_activities_table, back_populates='grounds')

    def __init__(self, source_id, name, district, address, website, hasMusic, hasWifi, hasToilet, hasEatery, hasDressingRoom, hasLighting, paid, latitude, longitude):
        self.source_id = source_id
        self.name = name
        self.district = district
        self.address = address
        self.website = website
        self.hasMusic = hasMusic
        self.hasWifi = hasWifi
        self.hasToilet = hasToilet
        self.hasEatery = hasEatery
        self.hasDressingRoom = hasDressingRoom
        self.hasLighting = hasLighting
        self.paid = paid

        self.latitude = latitude
        self.longitude =longitude

       # self.user_id = user_id
        self.create_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        """
        Persist a ground in the database
        :return:
        """
        db.session.add(self)
        db.session.commit()

    def update(self, name, district, address, website, hasMusic, hasWifi, hasToilet, hasEatery, hasDressingRoom, hasLighting, paid):
        """
        Update the name of the Ground
        :param name:
        :return:
        """
        self.name = name
        self.district = district
        self.address = address
        self.website = website
        self.hasMusic = hasMusic
        self.hasWifi = hasWifi
        self.hasToilet = hasToilet
        self.hasEatery = hasEatery
        self.hasDressingRoom = hasDressingRoom
        self.hasLighting = hasLighting
        self.paid = paid
        db.session.commit()

    def delete(self):
        """
        Delete a Bucket from the database
        :return:
        """
        db.session.delete(self)
        db.session.commit()

    def json(self):
        """
        Json representation of the bucket model.
        :return:
        """
        return {
            'id': self.id,
            'source_id': self.source_id,
            'name': self.name,
            'district': self.district,
            'createdAt': self.create_at.isoformat(),
            'modifiedAt': self.modified_at.isoformat()
        }

    @staticmethod
    def get_by_source_id(source_id):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return Ground.query.filter_by(source_id=source_id).first()

class Activity(db.Model):

    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    create_at = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)

    grounds = db.relationship('Ground', secondary=grounds_to_activities_table, back_populates='activities')

    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description

        self.create_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        """
        Persist Item into the database
        :return:
        """
        db.session.add(self)
        db.session.commit()

    def update(self, name, description=None):
        """
        Update the records in the item
        :param name: Name
        :param description: Description
        :return:
        """
        self.name = name
        if description is not None:
            self.description = description
        db.session.commit()

    def delete(self):
        """
        Delete an item
        :return:
        """
        db.session.delete(self)
        db.session.commit()

    def json(self):
        """
        Json representation of the model
        :return:
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

    @staticmethod
    def get_by_id(id):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return Activity.query.filter_by(id=id).first()

class ActivitiesEnum(Enum):
    easy_training = 1
    football = 2
    hockey = 3
    basketball = 4
    skating = 5
    ice_skating = 6
    workout = 7
    yoga = 8
    box = 9

    @property
    def description(self):
        if self is ActivitiesEnum.easy_training:
            return ''
        if self is ActivitiesEnum.football:
            return ''
        if self is ActivitiesEnum.hockey:
            return ''
        if self is ActivitiesEnum.basketball:
            return ''
        if self is ActivitiesEnum.skating:
            return ''
        if self is ActivitiesEnum.ice_skating:
            return ''
        if self is ActivitiesEnum.workout:
            return ''
        if self is ActivitiesEnum.yoga:
            return ''
        if self is ActivitiesEnum.box:
            return ''

    @property
    def persistent(self):
        return Activity.get_by_id(self.value)