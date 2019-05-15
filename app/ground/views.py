from flask import Blueprint, request, abort
from app.auth.helper import token_required
from app.ground.helper import begin_sheduled_updating_grounds_dataset, response, response_for_ground, response_for_grounds, get_ground_json_list, \
    get_ground_geojson_list, response_with_pagination, paginate_grounds
from app.models import User, Ground

# Initialize blueprint
ground = Blueprint('ground', __name__)

@ground.record
def record(state):
    begin_sheduled_updating_grounds_dataset(state)

@ground.route('/grounds/', methods=['GET'])
@token_required
def grounds(current_user):
    """
    Return all grounds on order to closing distance to user and limit them to 10.
    :param current_user:
    :return:
    """
    user = User.get_by_id(current_user.id)
    page = request.args.get('page', 1, type=int)

    latitude = request.args.get('latitude', None, type=float)
    longitude = request.args.get('longitude', None, type=float)

    items, nex, pagination, previous = paginate_grounds(current_user.id, page, latitude, longitude, user)

    if items:
        return response_with_pagination(get_ground_json_list(items), previous, nex, pagination.total)
    return response_with_pagination([], previous, nex, 0)


@ground.route('/grounds/geo', methods=['POST'])
@token_required
def grounds_geography(current_user):
    """
    Create a Ground from the sent json data.
    :param current_user: Current User
    :return:
    """
    if request.content_type == 'application/json':
        data = request.get_json()

        frame = data.get('geobounds')

        if frame:
            # northEast point
            northEast = frame.get('northEast')

            if not northEast:
                return response('failed', 'Missing northEast attribute', 400)

            ne_latitude = northEast.get('latitude')
            ne_longitude = northEast.get('longitude')

            if not ne_latitude:
                return response('failed', 'Missing latitude attribute for northEast point', 400)

            if not ne_longitude:
                return response('failed', 'Missing longitude attribute for northEast point', 400)
            
            # southWest point
            southWest = frame.get('southWest')

            if not southWest:
                return response('failed', 'Missing southWest attribute', 400)

            sw_latitude = southWest.get('latitude')
            sw_longitude = southWest.get('longitude')

            if not sw_latitude:
                return response('failed', 'Missing latitude attribute for southWest point', 400)

            if not sw_longitude:
                return response('failed', 'Missing longitude attribute for southWest point', 400)
            
            try:
                float(ne_latitude)
                float(ne_longitude)
                float(sw_latitude)
                float(sw_longitude)
            except ValueError:
                return response('failed', 'Wrong coordinates values type', 400)

            grounds = Ground.get_by_location_rect(ne_latitude, ne_longitude, sw_latitude, sw_longitude)
            if not grounds:
                grounds = []

            return response_for_grounds(get_ground_geojson_list(grounds))
        return response('failed', 'Missing feobounds attribute', 400)
    return response('failed', 'Content-type must be json', 202)


@ground.route('/grounds/<ground_id>', methods=['GET'])
@token_required
def get_ground(current_user, ground_id):
    """
    Return a user ground with the supplied user Id.
    :param current_user: User
    :param ground_id: ground Id
    :return:
    """
    try:
        int(ground_id)
    except ValueError:
        return response('failed', 'Please provide a valid Ground Id', 400)
    else:
        ground = Ground.get_by_id(ground_id)
        if ground:
            return response_for_ground(ground.json())
        return response('failed', "Ground not found", 404)


@ground.errorhandler(404)
def handle_404_error(e):
    """
    Return a custom message for 404 errors.
    :param e:
    :return:
    """
    return response('failed', 'Ground resource cannot be found', 404)


@ground.errorhandler(400)
def handle_400_errors(e):
    """
    Return a custom response for 400 errors.
    :param e:
    :return:
    """
    return response('failed', 'Bad Request', 400)
