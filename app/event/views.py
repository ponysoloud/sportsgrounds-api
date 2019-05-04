from dateutil.parser import isoparse
from flask import Blueprint, request, abort
from app.auth.helper import token_required
from app.event.helper import response, response_for_event, response_for_created_event, response_with_pagination, get_event_json_list, paginate_events
from app.models import User, Ground, Activity, Event, TrainingEvent, MatchEvent, TourneyEvent, EventType, EventStatus, EventParticipantsLevel, Team

# Initialize blueprint
event = Blueprint('event', __name__)

@event.route('/events', methods=['GET'])
@token_required
def events(current_user):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty Grounds object if user has no grounds
    :param current_user:
    :return:
    """
    page = request.args.get('page', 1, type=int)

    ground = request.args.get('groundId', None, type=int)
    status = request.args.get('status', None, type=int)
    type = request.args.get('type', None, type=int)
    activity = request.args.get('activity', None, type=int)
    user = request.args.get('userId', None, type=int)

    items, nex, pagination, previous = paginate_events(page, ground, status, type, activity, user)

    if items:
        return response_with_pagination(get_event_json_list(items), previous, nex, pagination.total)
    return response_with_pagination([], previous, nex, 0)


@event.route('/events', methods=['POST'])
@token_required
def create_event(current_user):
    """
    Create a Bucket from the sent json data.
    :param current_user: Current User
    :return:
    """
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
            event = Event.initTraining(user, title, description, activity, participants_level, participants_age_from, participants_age_to, begin_at, end_at)
            event.ground = ground
            event.save()
        elif event_type is EventType.match:
            event = Event.initMatch(user, title, description, activity, participants_level, participants_age_from, participants_age_to, begin_at, end_at)
            event.ground = ground
            event.save()
        elif event_type is EventType.tourney:
            teams_count = event_value.get('teamsCount', 3)

            try:
                int(teams_count)
            except ValueError:
                return response('failed', "Wrong teamsCount attribute type", 400)

            event = Event.initTourney(user, title, description, activity, participants_level, participants_age_from, participants_age_to, begin_at, end_at, teams_count)
            event.ground = ground
            event.save()

        return response_for_created_event(event, 201)
    return response('failed', 'Content-type must be json', 202)

@event.route('/events/<event_id>', methods=['GET'])
@token_required
def get_event(current_user, event_id):
    """
    Return a user ground with the supplied user Id.
    :param current_user: User
    :param ground_id: ground Id
    :return:
    """
    try:
        int(event_id)
    except ValueError:
        return response('failed', 'Please provide a valid Event Id', 400)
    else:
        event = Event.get_by_id(event_id)
        if event:
            return response_for_event(event.json())
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
            return response('failed', 'The Event with Id ' + event_id + ' does not exist', 404)

        if title or description:
            event.update(title, description)
            
        if teams_count:
            if event.type is EventType.tourney:
                event.subevent.update(teams_count)
            else:
                return response('failed', 'No attribute or value was specified, nothing was changed', 400)

        return response_for_created_event(event, 201)
    return response('failed', 'Content-type must be json', 202)


@event.route('/events/<event_id>', methods=['DELETE'])
@token_required
def delete_event(current_user, event_id):
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
    event = User.get_by_id(current_user.id).events.filter_by(id=event_id).first()
    if not event:
        abort(404)
    event.delete()
    return response('success', 'Event successfully deleted', 200)


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
