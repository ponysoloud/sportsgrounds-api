import datetime
import jwt
import math
from enum import Enum
from app import app, db, bcrypt
from sqlalchemy import orm, func, and_, or_, case
from sqlalchemy.sql import expression
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.associationproxy import association_proxy

team_participants_table = db.Table('teamparticipants', db.Model.metadata,
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'), primary_key=True),
    db.Column('paricipant_id', db.Integer, db.ForeignKey('users.id'), primary_key=True) 
)

user_ratings_table = db.Table('userratings', db.Model.metadata,
    db.Column('rated_user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('rated_by_user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True) 
)

class User(db.Model):
    """
    Table schema
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    name = db.Column(db.Text, nullable=False)
    surname = db.Column(db.Text, nullable=False)

    birthday = db.Column(db.DateTime, nullable=False)
    image_url = db.Column(db.Text, nullable=True)
    
    rating = db.Column(db.Integer, default=0, nullable=False)

    registered_on = db.Column(db.DateTime, nullable=False)

    buckets = db.relationship('Bucket', backref='bucket', lazy='dynamic')

    events = db.relationship('Event', back_populates='owner', lazy='dynamic')
    teams = db.relationship('Team', secondary=team_participants_table, back_populates='participants', lazy='dynamic')
    messages = db.relationship('EventMessage', back_populates='sender', order_by='desc(EventMessage.create_at)', lazy='dynamic')

    rated_by_me_users = db.relationship('User',
                            secondary=user_ratings_table,
                            primaryjoin=id==user_ratings_table.c.rated_user_id,
                            secondaryjoin=id==user_ratings_table.c.rated_by_user_id,
                            backref="rated_me_users"
    )

    def __init__(self, email, password, name, surname, birthday, image_url=None):
        self.email = email
        self.password = bcrypt.generate_password_hash(password, app.config.get('BCRYPT_LOG_ROUNDS')).decode('utf-8')

        self.name = name
        self.surname = surname

        self.birthday = birthday
        self.image_url = image_url

        self.registered_on = datetime.datetime.utcnow()

    def save(self):
        """
        Persist the user in the database
        :param user:
        :return:
        """
        db.session.add(self)
        db.session.commit()
        return self.encode_auth_token(self.id)

    def update(self):
        db.session.commit()

    def json(self, other_user=None):
        json = {
            'name': self.name,
            'surname': self.surname,
            'image_url': self.image_url,
            'rating': len(self.rated_me_users)
        }

        if other_user:
            json['rated'] = self.rated_by_user(other_user)

        return json

    def personaljson(self):
        return {
            'email': self.email,
            'name': self.name,
            'surname': self.surname,
            'image_url': self.image_url,
            'rating': len(self.rated_me_users),
            'rated': self.rated_by_user(self)
        }

    def encode_auth_token(self, user_id):
        """
        Encode the Auth token
        :param user_id: User's Id
        :return:
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=app.config.get('AUTH_TOKEN_EXPIRY_DAYS'),
                                                                       seconds=app.config.get('AUTH_TOKEN_EXPIRY_SECONDS')),
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

    def reset_password(self, new_password):
        """
        Update/reset the user password.
        :param new_password: New User Password
        :return:
        """
        self.password = bcrypt.generate_password_hash(new_password, app.config.get('BCRYPT_LOG_ROUNDS')) \
            .decode('utf-8')
        db.session.commit()

    def rated_by_user(self, user):
        if self.id == user.id:
            return True
        else:
            print(self.rated_me_users)
            return user in self.rated_me_users

    @hybrid_property
    def age(self):
        today = datetime.datetime.utcnow()
        return today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))

    @age.expression
    def age(cls):
        return func.datediff(text('year'), utcnow(), cls.birthday)

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

    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    create_at = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)

    gactivities = db.relationship('GroundActivity', back_populates='ground', collection_class=set, cascade="all, delete-orphan")
    events = db.relationship('Event', back_populates='ground')

    activities = association_proxy('gactivities', 'activity')

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
        self.longitude = longitude

        self.create_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

        #non orm field
        self.distance = None

    @orm.reconstructor
    def init_on_load(self):
        #non orm field
        self.distance = None

    @hybrid_method
    def distance_to(self, lat, lng):
        return gc_distance(lat, lng, self.latitude, self.longitude)

    @distance_to.expression
    def distance_to(cls, lat, lng):
        return gc_distance(lat, lng, cls.latitude, cls.longitude, math=func)

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
        Json representation of the ground model.
        :return:
        """
        json = {
            'id': self.id,
            'source_id': self.source_id,
            'name': self.name,
            'district': self.district,
            'address': self.address,
            'website': self.website,
            'hasMusic': self.hasMusic,
            'hasWifi': self.hasWifi,
            'hasToilet': self.hasToilet,
            'hasEatery': self.hasEatery,
            'hasDressingRoom': self.hasDressingRoom,
            'hasLighting': self.hasLighting,
            'paid': self.paid,
            'activities': list(map(lambda a: a.value, self.activities)),
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude
            }
        }

        if self.distance:
            json['distance'] = self.distance

        return json

    def geojson(self):
        """
        Json representation of the ground model.
        :return:
        """
        return {
            'id': self.id,
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude
            }
        }

    @staticmethod
    def get_by_id(id):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return Ground.query.filter_by(id=id).first()

    @staticmethod
    def get_by_source_id(source_id):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return Ground.query.filter_by(source_id=source_id).first()

    @staticmethod
    def get_by_location_rect(alatitude, alongitude, blatitude, blongitude):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return Ground.query.filter(and_(Ground.latitude >= min(alatitude, blatitude), Ground.latitude <= max(alatitude, blatitude))) \
            .filter(and_(Ground.longitude >= min(alongitude, blongitude), Ground.longitude <= max(alongitude, blongitude))).all()

def gc_distance(lat1, lng1, lat2, lng2, math=math):
        ang = math.acos(math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                        math.cos(math.radians(lng2) - math.radians(lng1)) +
                        math.sin(math.radians(lat1)) * math.sin(math.radians(lat2)))
        return 6371 * ang

# ACTIVITY

class Activity(Enum):
    easy_training = 1
    football = 2
    hockey = 3
    basketball = 4
    skating = 5
    ice_skating = 6
    workout = 7
    yoga = 8
    box = 9

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    @property
    def eventTypes(self):
        if self is Activity.easy_training:
            return [EventType.training]
        if self is Activity.football:
            return [EventType.training, EventType.match, EventType.tourney]
        if self is Activity.hockey:
            return [EventType.training, EventType.match, EventType.tourney]
        if self is Activity.basketball:
            return [EventType.training, EventType.match, EventType.tourney]
        if self is Activity.skating:
            return [EventType.training]
        if self is Activity.ice_skating:
            return [EventType.training]
        if self is Activity.workout:
            return [EventType.training]
        if self is Activity.yoga:
            return [EventType.training]
        if self is Activity.box:
            return [EventType.training]

    @property
    def title(self):
        if self is Activity.easy_training:
            return 'Легкая тренировка'
        if self is Activity.football:
            return 'Футбол'
        if self is Activity.hockey:
            return 'Хоккей'
        if self is Activity.basketball:
            return 'Баскетбол'
        if self is Activity.skating:
            return 'Катание'
        if self is Activity.ice_skating:
            return 'Катание на коньках'
        if self is Activity.workout:
            return 'Воркаут'
        if self is Activity.yoga:
            return 'Йога'
        if self is Activity.box:
            return 'Бокс'

    @property
    def description(self):
        if self is Activity.easy_training:
            return ''
        if self is Activity.football:
            return ''
        if self is Activity.hockey:
            return ''
        if self is Activity.basketball:
            return ''
        if self is Activity.skating:
            return ''
        if self is Activity.ice_skating:
            return ''
        if self is Activity.workout:
            return ''
        if self is Activity.yoga:
            return ''
        if self is Activity.box:
            return ''

    @property
    def json(self):
        """
        Json representation of the model
        :return:
        """
        return {
            'id': self.value,
            'title': self.title,
            'description': self.description
        }

class GroundActivity(db.Model):

    __tablename__ = 'groundactivities'

    ground_id = db.Column(db.Integer, db.ForeignKey('grounds.id'), primary_key=True)
    activity = db.Column(db.Enum(Activity), primary_key=True)

    ground = db.relationship('Ground', back_populates='gactivities')

    def __hash__(self):
        return hash((self.__class__, self.activity.name))

    def __init__(self, activity):
        self.activity = activity

# EVENT

class EventType(Enum):
    training = 1
    match = 2
    tourney = 3

    @property
    def title(self):
        if self is EventType.training:
            return 'Тренировка'
        if self is EventType.match:
            return 'Простая игра'
        if self is EventType.tourney:
            return 'Турнир'
    
class EventStatus(Enum):
    scheduled = 1
    processing = 2
    ended = 3
    canceled = 4

    @property
    def title(self):
        if self is EventStatus.scheduled:
            return 'Запланировано'
        if self is EventStatus.in_process:
            return 'В процессе'
        if self is EventStatus.ended:
            return 'Завершилось'
        if self is EventStatus.canceled:
            return 'Отменено'

class EventParticipantsLevel(Enum):
    beginner = 1
    average = 2
    experienced  = 3
    expert = 4
    any = 5

    @property
    def title(self):
        if self is EventParticipantsLevel.beginner:
            return 'Начинающий'
        if self is EventParticipantsLevel.average:
            return 'Средний'
        if self is EventParticipantsLevel.experienced:
            return 'Опытный'
        if self is EventParticipantsLevel.expert:
            return 'Профессионал'
        if self is EventParticipantsLevel.any:
            return 'Любой'

class Event(db.Model):

    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    activity = db.Column(db.Enum(Activity), nullable=False)
    type = db.Column(db.Enum(EventType), nullable=False)

    participants_level = db.Column(db.Enum(EventParticipantsLevel), nullable=False)
    participants_age_from = db.Column(db.Integer, nullable=False)
    participants_age_to = db.Column(db.Integer, nullable=False)

    ground_id = db.Column(db.Integer, db.ForeignKey('grounds.id'))

    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)

    canceled = db.Column(db.Boolean, nullable=False, default=False)
    
    begin_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=False)

    create_at = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)

    owner = db.relationship('User', back_populates='events')
    ground = db.relationship('Ground', back_populates='events')
    messages = db.relationship('EventMessage', back_populates='event', order_by='desc(EventMessage.create_at)', lazy='dynamic')

    def __init__(self, user, title, description, activity, type, participants_level, participants_age_from, participants_age_to, begin_at, end_at):
        self.owner = user
        self.title = title
        self.description = description
        self.activity = activity
        self.type = type
        self.participants_level = participants_level
        self.participants_age_from = participants_age_from
        self.participants_age_to = participants_age_to
        self.begin_at = begin_at
        self.end_at = end_at

        self.create_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        """
        Persist Item into the database
        :return:
        """
        db.session.add(self)
        db.session.commit()

    def update(self, title=None, description=None):
        """
        Update the records in the item
        :param name: Name
        :param description: Description
        :return:
        """
        if title is not None:
            self.title = title
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
        event_json = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'activity': self.activity.value,
            str(self.type.name): self.subevent.json(),
            'requiredLevel': self.participants_level.value,
            'requiredAgeFrom': self.participants_age_from,
            'requiredAgeTo': self.participants_age_to,
            'groundId': self.ground_id,
            'status': self.status.value,
            'beginAt': self.begin_at.isoformat(),
            'endAt': self.end_at.isoformat(),
            'createdAt': self.create_at.isoformat(),
            'modifiedAt': self.modified_at.isoformat()
        }

        return {
            'eventType': self.type.value,
            'event': event_json
        }

    @hybrid_property
    def status(self):
        today = datetime.datetime.utcnow()

        if self.canceled:
            return EventStatus.canceled
        elif today < self.begin_at:
            return EventStatus.scheduled
        elif today <= self.end_at:
            return EventStatus.processing
        else:
            return EventStatus.ended

    @status.expression
    def status(cls):
        return case(
            [
                (cls.canceled == True, EventStatus.canceled.name),
                (and_(cls.canceled == False, utcnow() < cls.begin_at), EventStatus.scheduled.name),
                (and_(cls.canceled == False, utcnow() <= cls.end_at, utcnow() >= cls.begin_at), EventStatus.processing.name),
            ],
            else_=EventStatus.ended.name)

    @property
    def subevent(self):
        if self.type is EventType.training:
            return self.training
        if self.type is EventType.match:
            return self.match
        if self.type is EventType.tourney:
            return self.tourney

    @property
    def teams(self):
        if self.type is EventType.training:
            return [self.training.team]
        if self.type is EventType.match:
            return [self.match.team_a, self.match.team_b]
        if self.type is EventType.tourney:
            return self.tourney.teams

    @staticmethod
    def init_training(user, title, description, activity, participants_level, participants_age_from, participants_age_to, begin_at, end_at, max_participants):
        event = Event(user, title, description, activity, EventType.training, participants_level, participants_age_from, participants_age_to, begin_at, end_at)
        training = TrainingEvent(max_participants)
        training.team.participants.append(user)
        event.training = training
        
        return event

    @staticmethod
    def init_match(user, title, description, activity, participants_level, participants_age_from, participants_age_to, begin_at, end_at, teams_size):
        event = Event(user, title, description, activity, EventType.match, participants_level, participants_age_from, participants_age_to, begin_at, end_at)
        match = MatchEvent(teams_size)
        match.teamA.participants.append(user)
        event.match = match

        return event

    @staticmethod
    def init_tourney(user, title, description, activity, participants_level, participants_age_from, participants_age_to, begin_at, end_at, teams_size, teams_count=3):
        event = Event(user, title, description, activity, EventType.tourney, participants_level, participants_age_from, participants_age_to, begin_at, end_at)
        tourney = TourneyEvent(teams_size, teams_count)
        tourney.teams.first().participants.append(user)
        event.tourney = tourney

        return event

    @staticmethod
    def get_by_id(id):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return Event.query.filter_by(id=id).first()

    @staticmethod
    def datetime_interval_free(begin, end, ground):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return len(Event.query.filter(or_(and_(Event.begin_at >= begin, Event.begin_at <= end), and_(Event.end_at > begin, Event.end_at < end))).filter_by(ground_id=ground.id).all())==0

class utcnow(expression.FunctionElement):
    type = db.DateTime()

@compiles(utcnow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"

class TrainingEvent(db.Model):
    __tablename__ = 'trainingevents'
    
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))

    event = db.relationship('Event', backref=orm.backref('training', uselist=False, cascade="all, delete-orphan", single_parent=True))
    team = db.relationship('Team', backref=orm.backref('training', uselist=False), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, max_participants):
        self.team = Team(max_participants)

    def json(self):
        """
        Json representation of the model
        :return:
        """
        return self.team.json()

class MatchEvent(db.Model):
    __tablename__ = 'matchevents'

    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), primary_key=True)

    team_a_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    team_b_id = db.Column(db.Integer, db.ForeignKey('teams.id'))

    team_a_score = db.Column(db.Integer, nullable=True)
    team_b_score = db.Column(db.Integer, nullable=True)

    event = db.relationship('Event', backref=orm.backref('match', uselist=False, cascade="all, delete-orphan", single_parent=True))
    team_a = db.relationship('Team', backref=orm.backref('match_a', uselist=False), foreign_keys=[team_a_id], cascade="all, delete-orphan", single_parent=True)
    team_b = db.relationship('Team', backref=orm.backref('match_b', uselist=False), foreign_keys=[team_b_id], cascade="all, delete-orphan", single_parent=True)

    def __init__(self, teams_size):
        self.team_a = Team(team_size)
        self.team_b = Team(team_size)

    def update(self, scoreA, scoreB):
        """
        Update the records in the item
        :param name: Name
        :param description: Description
        :return:
        """
        self.team_a_score = scoreA
        self.team_b_score = scoreB
        db.session.commit()

    def json(self):
        """
        Json representation of the model
        :return:
        """
        return {
            'scoreA': self.team_a_score,
            'scoreB': self.team_b_score,
            'teamA': self.team_a.json(),
            'teamB': self.team_b.json()
        }
    
class TourneyEvent(db.Model):
    __tablename__ = 'tourneyevents'

    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), primary_key=True)

    event = db.relationship('Event', backref=orm.backref('tourney', uselist=False, cascade="all, delete-orphan"))
    teams = db.relationship('Team', backref='tourney', cascade="all, delete-orphan", single_parent=True)

    def __init__(self, teams_size, teams_count=3):
        self.teams = [Team(teams_size) for i in range(teams_count)]

    def update(self, teams_count):
        teams_diff = teams_count - len(self.teams)
        if teams_diff > 0:
            for i in range(teams_diff):
                self.teams.append(Team())

    def json(self):
        """
        Json representation of the model
        :return:
        """
        return {
            'teamsCount': len(self.teams),
            'teams': list(map(lambda t: t.json(), self.teams))
        }

class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    max_participants = db.Column(db.Integer, nullable=False)

    tourney_id = db.Column(db.Integer, db.ForeignKey('tourneyevents.event_id'), nullable=True)

    create_at = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)

    participants = db.relationship('User', secondary=team_participants_table, back_populates='teams', lazy='dynamic')

    def __init__(self, max_participants):
        self.max_participants = max_participants

        self.create_at = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        """
        Persist Item into the database
        :return:
        """
        db.session.add(self)
        db.session.commit()

    def update(self):
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
            'maxParticipants': self.max_participants,
            'participants': list(map(lambda p: p.json(), self.participants))
        }

    @property
    def match(self):
        if self.match_a:
            return self.match_a
        else:
            return self.match_b

    @property
    def event(self):
        if self.tourney:
            return self.tourney.event
        if self.match:
            return self.match.event
        if self.training:
            return self.training.event

    @property
    def is_full(self):
        return len(self.participants) == self.max_participants

    @staticmethod
    def get_by_id(id):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return Team.query.filter_by(id=id).first()

class EventMessage(db.Model):
    __tablename__ = 'eventmessages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    text = db.Column(db.Text, nullable=False)

    create_at = db.Column(db.DateTime, nullable=False)

    event = db.relationship('Event', back_populates='messages')
    sender = db.relationship('User', back_populates='messages')

    def __init__(self, sender, text):
        self.sender = sender
        self.text = text

        self.create_at = datetime.datetime.utcnow()

    def save(self):
        """
        Persist Item into the database
        :return:
        """
        db.session.add(self)
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
            'eventId': self.event_id,
            'sender': self.sender.json(),
            'text': self.text,
            'createdAt': self.create_at.isoformat()
        }