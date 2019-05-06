import os
import requests
from datetime import datetime, date
from flask import make_response, jsonify, url_for
from flask_sqlalchemy import BaseQuery
from app import app, db
from app.models import Event, EventStatus, EventType, Ground, User

def response(status, message, code):
    """
    Helper method to make a http response
    :param status: Status message
    :param message: Response message
    :param code: Response status code
    :return: Http Response
    """
    return make_response(jsonify({
        'status': status,
        'message': message
    })), code

def response_for_event(event):
    """
    Return the response for when a single bucket when requested by the user.
    :param user_bucket:
    :return:
    """
    return make_response(jsonify({
        'status': 'success',
        'event': event
    }))
    
def response_for_created_event(event, status_code):
    """
    Method returning the response when a bucket has been successfully created.
    :param status_code:
    :param user_bucket: Bucket
    :return: Http Response
    """
    return make_response(jsonify({
        'status': 'success',
        'event': event.json()
    })), status_code

def response_for_created_message(message, status_code):
    """
    Method returning the response when a bucket has been successfully created.
    :param status_code:
    :param user_bucket: Bucket
    :return: Http Response
    """
    return make_response(jsonify({
        'status': 'success',
        'message': message.json()
    })), status_code

def get_event_json_list(events):
    """
    Make json objects of the grounds and add them to a list.
    :param user_buckets: Bucket
    :return:
    """
    json_list = []
    for event in events:
        json_list.append(event.json())
    return json_list

def get_message_json_list(messages):
    """
    Make json objects of the grounds and add them to a list.
    :param user_buckets: Bucket
    :return:
    """
    json_list = []
    for message in messages:
        json_list.append(message.json())
    return json_list

def extract_parameters_from_socket_event_data(data):
    token = data.get('token')
        
    if not token:
        return None, None, 'Token is missing'

    decode_response = None
    try:
        decode_response = User.decode_auth_token(token)
        current_user = User.query.filter_by(id=decode_response).first()
    except:
        message = 'Invalid token'
        if isinstance(decode_response, str):
            message = decode_response
        return None, None, message

    event_id = data.get('eventId')

    try:
        int(event_id)
    except ValueError:
        return None, None, 'Invalid Event Id'

    event = Event.get_by_id(event_id)

    if not event:
        return None, None, 'Event cannot be found'

    return current_user, event, None

def response_with_pagination_events(events, previous, nex, count):
    """
    Make a http response for BucketList get requests.
    :param count: Pagination Total
    :param nex: Next page Url if it exists
    :param previous: Previous page Url if it exists
    :param buckets: Bucket
    :return: Http Json response
    """
    return make_response(jsonify({
        'status': 'success',
        'previous': previous,
        'next': nex,
        'count': count,
        'events': events
    })), 200

def response_with_pagination_messages(messages, previous, nex, count):
    """
    Make a http response for BucketList get requests.
    :param count: Pagination Total
    :param nex: Next page Url if it exists
    :param previous: Previous page Url if it exists
    :param buckets: Bucket
    :return: Http Json response
    """
    return make_response(jsonify({
        'status': 'success',
        'previous': previous,
        'next': nex,
        'count': count,
        'messages': messages
    })), 200

def paginate_events(page, ground_id, status_value, activity_value, type_value, user_id):
    """
    Get a user by Id, then get hold of their buckets and also paginate the results.
    There is also an option to search for a bucket name if the query param is set.
    Generate previous and next pagination urls
    :param q: Query parameter
    :param user_id: User Id
    :param user: Current User
    :param page: Page number
    :return: Pagination next url, previous url and the user buckets.
    """

    ground = Ground.get_by_id(ground_id) if ground_id else None
    status = EventStatus(status_value) if status_value else None
    activity = Activity(activity_value) if activity_value else None
    type = EventType(type_value) if type_value else None
    user = User.get_by_id(user_id) if user_id else None

    events_query = Event.query

    if ground:
        events_query = events_query.filter_by(ground_id=ground.id)

    if activity:
        events_query = events_query.filter_by(activity=activity)

    if type:
        events_query = events_query.filter_by(type=type)

    if user:
        events_query = events_query.filter_by(owner=user)

    if status:
        if status is EventStatus.scheduled or status is EventStatus.processing:
            events_query = events_query.order_by(Event.begin_at)

        if status is EventStatus.ended:
            events_query = events_query.order_by(Event.end_at.desc())

        event_status = Event.status.label('status')
        events_query = db.session.query(Event, event_status).filter(event_status==status.name)
        event_status = BaseQuery(events_query.subquery(), db.session())

    pagination = events_query.paginate(page=page, per_page=app.config['EVENTS_PER_PAGE'], error_out=False)

    previous = None
    if pagination.has_prev:
        previous = url_for('event.events', groundId=ground_id, status=status_value, activity=activity_value, type=type_value, userId=user_id, page=page-1, _external=True)

    nex = None
    if pagination.has_next:
        nex = url_for('event.events', groundId=ground_id, status=status_value, activity=activity_value, type=type_value, userId=user_id, page=page+1, _external=True)
            
    items = pagination.items

    if status:
        items = list(map(lambda r: r.Event, items))

    return items, nex, pagination, previous

def paginate_messages(page, event, user_id):
    """
    Get a user by Id, then get hold of their buckets and also paginate the results.
    There is also an option to search for a bucket name if the query param is set.
    Generate previous and next pagination urls
    :param q: Query parameter
    :param user_id: User Id
    :param user: Current User
    :param page: Page number
    :return: Pagination next url, previous url and the user buckets.
    """

    pagination = event.messages \
        .paginate(page=page, per_page=app.config['EVENTS_PER_PAGE'], error_out=False)

    previous = None
    if pagination.has_prev:
        previous = url_for('event.get_event_messages', event_id=event.id, page=page-1, _external=True)

    nex = None
    if pagination.has_next:
        nex = url_for('event.get_event_messages', event_id=event.id, type=type_value, page=page+1, _external=True)
            
    items = pagination.items
    return items, nex, pagination, previous
