import os
import requests
from datetime import datetime, date
from flask import make_response, jsonify, url_for
from flask_sqlalchemy import BaseQuery
from sqlalchemy import orm, func, and_, or_, case
from app import app, db
from app.models import Event, EventStatus, EventType, TrainingEvent, MatchEvent, TourneyEvent, Ground, User, Team, Activity

def response(status, message, code):
    return make_response(jsonify({
        'status': status,
        'message': message
    })), code

def response_for_event(event):
    return make_response(jsonify({
        'status': 'success',
        'event': event
    }))
    
def response_for_created_event(event, status_code):
    return make_response(jsonify({
        'status': 'success',
        'event': event
    })), status_code

def response_for_created_message(message, status_code):
    return make_response(jsonify({
        'status': 'success',
        'message': message.json()
    })), status_code

def get_event_json_list(events):
    json_list = []
    for event in events:
        json_list.append(event.short_json())
    return json_list

def get_message_json_list(messages):
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
    return make_response(jsonify({
        'status': 'success',
        'previous': previous,
        'next': nex,
        'count': count,
        'events': events
    })), 200

def response_with_pagination_messages(messages, previous, nex, skip, count):
    return make_response(jsonify({
        'status': 'success',
        'previous': previous,
        'next': nex,
        'count': count,
        'skip': skip,
        'messages': messages
    })), 200

def paginate_events(page, ground_id, status_value, type_value, activity_value, owner_id, participant_id):
    ground = Ground.get_by_id(ground_id) if ground_id else None
    status = EventStatus(status_value) if status_value else None
    activity = Activity(activity_value) if activity_value else None
    type = EventType(type_value) if type_value else None
    owner = User.get_by_id(owner_id) if owner_id else None
    participant = User.get_by_id(participant_id) if participant_id else None

    events_query = Event.query

    if participant:
        training_events_query = Event.query.join(TrainingEvent).join(Team).join(Team.participants).filter(User.id==participant_id)
        match_events_query = Event.query.join(MatchEvent).join(Team, or_(Team.id==MatchEvent.team_a_id, Team.id==MatchEvent.team_b_id)).join(Team.participants).filter(User.id==participant_id)
        tourney_events_query = Event.query.join(TourneyEvent).join(Team).join(Team.participants).filter(User.id==participant_id)

        events_query = training_events_query.union(match_events_query).union(tourney_events_query)

    if ground:
        events_query = events_query.filter_by(ground_id=ground.id)

    if activity:
        events_query = events_query.filter_by(activity=activity)

    if type:
        events_query = events_query.filter_by(type=type)

    if owner:
        events_query = events_query.filter_by(owner=owner)

    if status:
        events_query = events_query.filter(Event.status==status.value)

        if status is EventStatus.scheduled or status is EventStatus.processing:
            events_query = events_query.order_by(Event.begin_at)
        elif status is EventStatus.ended:
            events_query = events_query.order_by(Event.end_at.desc())
    else:
        events_query = events_query.order_by(Event.status)

    pagination = events_query.paginate(page=page, per_page=app.config['EVENTS_PER_PAGE'], error_out=False)

    previous = None
    if pagination.has_prev:
        previous = url_for('event.events', groundId=ground_id, status=status_value, activity=activity_value, type=type_value, ownerId=owner_id, participantId=participant_id, page=page-1, _external=True)

    nex = None
    if pagination.has_next:
        nex = url_for('event.events', groundId=ground_id, status=status_value, activity=activity_value, type=type_value, ownerId=owner_id, participantId=participant_id, page=page+1, _external=True)
            
    items = pagination.items

    return items, nex, pagination, previous

def paginate_messages(skip, count, event, user_id):
    limit = count
    if not limit:
        limit = app.config['MESSAGES_PER_PAGE']

    messages = event.messages.offset(skip).limit(limit).all()
    total_count = event.messages.count()

    previous = None
    if skip > 0:
        previous = url_for('event.get_event_messages', event_id=event.id, count=skip, skip=0, _external=True)

    nex = None
    if len(messages) + skip < total_count:
        nex = url_for('event.get_event_messages', event_id=event.id, count=limit, skip=skip + len(messages), _external=True)
            
    return messages, nex, previous, skip, len(messages)
