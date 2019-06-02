import json
from dateutil.parser import isoparse
from flask import Blueprint, request, abort
from flask_socketio import send, emit, join_room, leave_room
from app import sockets
from app.auth.helper import token_required
from app.event.helper import response, response_for_event, response_for_created_event, response_for_created_message, \
    response_with_pagination_events, response_with_pagination_messages, get_event_json_list, get_message_json_list, \
    paginate_events, paginate_messages, extract_parameters_from_socket_event_data
from app.models import User, Ground, Activity, Event, TrainingEvent, MatchEvent, TourneyEvent, EventType, EventStatus, \
    EventParticipantsLevel, Team, EventMessage

# Initialize blueprint
event = Blueprint('event', __name__)

@event.route('/events', methods=['GET'])
@token_required
def events(current_user):
    page = request.args.get('page', 1, type=int)

    ground = request.args.get('groundId', None, type=int)
    status = request.args.get('status', None, type=int)
    type = request.args.get('type', None, type=int)
    activity = request.args.get('activity', None, type=int)
    owner = request.args.get('ownerId', None, type=int)
    participant = request.args.get('participantId', None, type=int)

    items, nex, pagination, previous = paginate_events(page, ground, status, type, activity, owner, participant)

    if items:
        return response_with_pagination_events(get_event_json_list(items), previous, nex, pagination.total)
    return response_with_pagination_events([], previous, nex, 0)


@event.route('/events', methods=['POST'])
@token_required
def create_event(current_user):
    if request.content_type == 'application/json':
        user = User.get_by_id(current_user.id)

        data = request.get_json()
        
        #eventType parsing

        event_type_value = data.get('eventType')
        if not event_type_value:
            return response('failed', 'Missing eventType attribute', 400)
        
        try:
            event_type = EventType(int(event_type_value))
        except ValueError:
            return response('failed', "EventType not found", 404)


        #event parsing

        event_value = data.get('event')
        if not event_value:
            return response('failed', 'Missing event attribute', 400)

        if not isinstance(event_value, dict):
            return response('failed', 'Wrong event attribute format', 400)


        #title parsing

        title = event_value.get('title')
        if not title:
            return response('failed', 'Missing title attribute', 400)

        description = event_value.get('description')

        #activity parsing

        activity_value = event_value.get('activity')
        if not activity_value:
            return response('failed', 'Missing activity attribute', 400)
    
        try:
            activity = Activity(int(activity_value))
        except ValueError:
            return response('failed', "Activity not found", 404)

        if not event_type in activity.eventTypes:
            response('failed', 'Wrong eventType for given activity', 400)

        #participants_level parsing

        participants_level_value = event_value.get('participantsLevel')
        if not participants_level_value:
            return response('failed', 'Missing participantsLevel attribute', 400)
    
        try:
            participants_level = EventParticipantsLevel(int(participants_level_value))
        except ValueError:
            return response('failed', "EventParticipantsLevel not found", 404)
 
        #participants_age_from and participants_age_to parsing

        participants_age_from = event_value.get('participantsAgeFrom')
        participants_age_to = event_value.get('participantsAgeTo')

        if not participants_age_from or not participants_age_to:
            return response('failed', 'Missing participantsAge range attributes', 400)

        if not isinstance(participants_age_from, int) or not isinstance(participants_age_to, int):
            return response('failed', 'Wrong participantsAge range attributes types', 400)
            
        #begin_at parsing

        try:
            begin_at_value = event_value.get('beginAt')
            begin_at = isoparse(str(begin_at_value))
        except ValueError:
            return response('failed', 'Wrong beginAt attribute type', 400)

        #end_at parsing
        
        try:
            end_at_value = event_value.get('endAt')
            end_at = isoparse(str(end_at_value))
        except ValueError:
            return response('failed', 'Wrong endAt attribute type', 400)

        if not begin_at < end_at:
            return response('failed', 'Begin time should be less than end time', 400)

        #ground parsing

        ground_id = event_value.get('groundId')
        if not ground_id:
            return response('failed', 'Missing groundId attribute', 400)

        if not isinstance(ground_id, int):
            return response('failed', 'Wrong groundId attribute type', 400)

        ground = Ground.get_by_id(ground_id)

        if not ground:
            return response('failed', 'Ground not found', 404)

        if not activity in ground.activities:
            return response('failed', 'Ground isn\'t design for given activity', 400)

        if not Event.datetime_interval_free(begin_at, end_at, ground):
            return response('failed', 'Ground is busy at given time interval', 400)

        #parsing specified type attributes

        if event_type is EventType.training:
            participants_count = event_value.get('participantsCount', 5)

            try:
                int(participants_count)
            except ValueError:
                return response('failed', "Wrong participantsCount attribute type", 400)

            event = Event.init_training(user, title, description, activity, participants_level, participants_age_from, participants_age_to, begin_at, end_at, participants_count)
            event.ground = ground
            event.save()
        else:
            teams_size = event_value.get('teamsSize', 5)

            try:
                int(teams_size)
            except ValueError:
                return response('failed', "Wrong teamsSize attribute type", 400)

            if event_type is EventType.match:
                event = Event.init_match(user, title, description, activity, participants_level, participants_age_from, participants_age_to, begin_at, end_at, teams_size)
                event.ground = ground
                event.save()
            elif event_type is EventType.tourney:
                teams_count = event_value.get('teamsCount', 3)

                try:
                    int(teams_count)
                except ValueError:
                    return response('failed', "Wrong teamsCount attribute type", 400)

                event = Event.init_tourney(user, title, description, activity, participants_level, participants_age_from, participants_age_to, begin_at, end_at, teams_size, teams_count)
                event.ground = ground
                event.save()

        return response_for_created_event(event.json(user), 201)
    return response('failed', 'Content-type must be json', 202)

@event.route('/events/<event_id>', methods=['GET'])
@token_required
def get_event(current_user, event_id):
    try:
        int(event_id)
    except ValueError:
        return response('failed', 'Please provide a valid Event Id', 400)
    else:
        event = Event.get_by_id(event_id)
        if event:
            return response_for_event(event.json(current_user))
        return response('failed', "Event not found", 404)


@event.route('/events/<event_id>', methods=['PUT'])
@token_required
def edit_event(current_user, event_id):
    """
    Validate the bucket Id. Also check for the name attribute in the json payload.
    If the name exists update the bucket with the new name.
    :param current_user: Current User
    :param bucket_id: Bucket Id
    :return: Http Json response
    """
    if request.content_type == 'application/json':
        data = request.get_json()

        title = data.get('title')
        description = data.get('description')
        teams_count = data.get('teamsCount')

        if not title and not description and not teams_count:
            return response('failed', 'No attribute or value was specified to update', 400)

        if title:
            try:
                str(title)
            except ValueError:
                return response('failed', "Wrong title attribute type", 400)

        if description:
            try:
                str(description)
            except ValueError:
                return response('failed', "Wrong description attribute type", 400)

        if teams_count:
            try:
                int(teams_count)
            except ValueError:
                return response('failed', "Wrong teamsCount attribute type", 400)

        try:
            int(event_id)
        except ValueError:
            return response('failed', 'Please provide a valid Event Id', 400)

        event = User.get_by_id(current_user.id).events.filter_by(id=event_id).first()
        if not event:
            return response('failed', 'The Event with Id ' + event_id + ' does not exist for user', 404)

        if event == EventStatus.canceled:
            return response('failed', 'Event was canceled', 400)

        if event == EventStatus.ended:
            return response('failed', 'Event was ended', 400)

        if title or description:
            event.update(title, description)
            
        if teams_count:
            if event.type is EventType.tourney:
                event.subevent.update(teams_count)

        return response_for_created_event(event.json(current_user), 201)
    return response('failed', 'Content-type must be json', 202)


@event.route('/events/<event_id>', methods=['DELETE'])
@token_required
def delete_event(current_user, event_id):
    try:
        int(event_id)
    except ValueError:
        return response('failed', 'Please provide a valid Event Id', 400)
    event = User.get_by_id(current_user.id).events.filter_by(id=event_id).first()
    if not event:
        abort(404)
    event.cancel()
    return response_for_created_event(event.json(current_user), 201)
    #return response('success', 'Event successfully canceled', 200)


@event.route('/events/<event_id>/actions/join', methods=['POST'])
@token_required
def join_to_event(current_user, event_id):
    """
    Deleting a User Bucket from the database if it exists.
    :param current_user:
    :param bucket_id:
    :return:
    """
    team_id = request.args.get('teamId', None, type=int)

    try:
        int(event_id)
    except ValueError:
        return response('failed', 'Please provide a valid Event Id', 400)

    user = User.get_by_id(current_user.id)
    event = Event.get_by_id(event_id)
    if not event:
        abort(404)

    if event == EventStatus.canceled:
        return response('failed', 'Event was canceled', 400)

    if event == EventStatus.ended:
        return response('failed', 'Event was ended', 400)
    
    if team_id:
        team = Team.get_by_id(team_id)

        if not team:
            return response('failed', 'Team cannot be found', 404)

        if not team in event.teams:
            return response('failed', 'The Event with Id ' + event_id + ' doesn\'t have Team with Id ' + team_id, 404)

    elif event.type is EventType.training:
        team = event.training.team
    else:
        return response('failed', 'Event with given Id requires teamId to join', 404)
    
    #check requirements to join
    if not (event.participants_age_from <= user.age <= event.participants_age_to):
        return response('failed', 'User\'s age does\'t meet the requirements of the event', 400)

    if user in team.participants:
        return response('failed', 'User already joined to the team', 400)

    if team.is_full:
        return response('failed', 'Team is full', 400)

    # remove user from other team in event
    for t in event.teams:
        if user in t.participants:
            t.participants.remove(user)

    # add user to team
    team.participants.append(user)
    team.update()

    return response_for_created_event(event.json(current_user), 201)


@event.route('/events/<event_id>/actions/leave', methods=['POST'])
@token_required
def leave_from_event(current_user, event_id):
    """
    Deleting a User Bucket from the database if it exists.
    :param current_user:
    :param bucket_id:
    :return:
    """
    try:
        int(event_id)
    except ValueError:
        return response('failed', 'Please provide a valid Event Id', 400)

    user = User.get_by_id(current_user.id)
    event = Event.get_by_id(event_id)
    if not event:
        abort(404)

    if event == EventStatus.canceled:
        return response('failed', 'Event was canceled', 400)

    if event == EventStatus.ended:
        return response('failed', 'Event was ended', 400)

    if event.owner.id == user.id:
        event.cancel()
        return response_for_created_event(event.json(user), 201)

    team = None

    for t in event.teams:
        if user in t.participants:
            team = t
    
    if not team:
        return response('failed', 'Team to leave cannot be found', 404)

    team.participants.remove(user)
    team.update()

    return response_for_created_event(event.json(user), 201)


@event.route('/events/<event_id>/messages', methods=['GET'])
@token_required
def get_event_messages(current_user, event_id):
    """
    Deleting a User Bucket from the database if it exists.
    :param current_user:
    :param bucket_id:
    :return:
    """
    skip = request.args.get('skip', 0, type=int)
    count = request.args.get('count', None, type=int)

    try:
        int(event_id)
    except ValueError:
        return response('failed', 'Please provide a valid Event Id', 400)

    user = User.get_by_id(current_user.id)
    event = Event.get_by_id(event_id)
    if not event:
        abort(404)

    messages, nex, previous, skip, total = paginate_messages(skip, count, event, user)
    return response_with_pagination_messages(get_message_json_list(messages), previous, nex, skip, total)


@event.route('/events/<event_id>/messages', methods=['POST'])
@token_required
def create_event_message(current_user, event_id):
    """
    Deleting a User Bucket from the database if it exists.
    :param current_user:
    :param bucket_id:
    :return:
    """
    if request.content_type == 'application/json':
        try:
            int(event_id)
        except ValueError:
            return response('failed', 'Please provide a valid Event Id', 400)

        event = Event.get_by_id(event_id)
        if not event:
            return response('failed', 'The Event with Id ' + event_id + ' does not exist', 404)

        user = User.get_by_id(current_user.id)

        data = request.get_json()
        text = data.get('text')

        if not text:
            return response('failed', 'Missing text attribute', 400)

        try:
            str(text)
        except ValueError:
            return response('failed', "Wrong text attribute type", 400)

        message = EventMessage(user, text)
        event.messages.append(message)
        event.update()

        return response_for_created_message(message, 201)
    return response('failed', 'Content-type must be json', 202)

# Event chat

@sockets.on('join', namespace='/event/messages')
def on_join_event_chat(data):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    if isinstance(data, str):
        data = json.loads(data)

    user, event, error = extract_parameters_from_socket_event_data(data)

    if error:
        emit('status', {
            'status': 'failed',
            'message': error
        }, room=request.sid)
    else:
        join_room(event.id)

        emit('joined', {
            'status': 'success',
            'user': user.json()
        }, room=event.id)


@sockets.on('message', namespace='/event/messages')
def message(data):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    if isinstance(data, str):
        data = json.loads(data)

    user, event, error = extract_parameters_from_socket_event_data(data)

    if error:
        emit('status', {
            'status': 'failed',
            'message': error
        }, room=request.sid)
    else:
        message = data.get('message')
    
        if message and isinstance(message, str):
            event_message = EventMessage(user, message)
            event.messages.append(event_message)
            event.update()

            emit('message', {
                'status': 'success',
                'newMessage': event_message.json()
            }, room=event.id)
        else:
            emit('message', {
                'status': 'failed',
                'message': 'Wrong type of Message attribute'
            }, room=event.id)


@sockets.on('leave', namespace='/event/messages')
def on_leave_event_chat(data):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    if isinstance(data, str):
        data = json.loads(data)

    user, event, error = extract_parameters_from_socket_event_data(data)

    if error:
        emit('status', {
            'status': 'failed',
            'message': error
        }, room=request.sid)
    else:
        leave_room(event.id)

        emit('leaved', {
            'status': 'success',
            'user': user.json()
        }, room=event.id)


@event.errorhandler(404)
def handle_404_error(e):
    """
    Return a custom message for 404 errors.
    :param e:
    :return:
    """
    return response('failed', 'Event cannot be found', 404)


@event.errorhandler(400)
def handle_400_errors(e):
    """
    Return a custom response for 400 errors.
    :param e:
    :return:
    """
    return response('failed', 'Bad Request', 400)
