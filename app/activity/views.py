from flask import Blueprint, request, abort
from app.auth.helper import token_required
from app.activity.helper import response, response_for_activity, response_for_activities, get_activity_json_list
from app.models import Activity

# Initialize blueprint
activity = Blueprint('activity', __name__)


@activity.route('/activities', methods=['GET'])
@token_required
def activities(current_user):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty activities object if user has no buckets
    :param current_user:
    :return:
    """
    return response_for_activities(get_activity_json_list(Activity))


@activity.route('/activities/<activity_id>', methods=['GET'])
@token_required
def get_activity(current_user, activity_id):
    """
    Return an activity object for the supplied activity id.
    :param current_user: User
    :param activity_id: Activity Id
    :return:
    """
    try:
        activity = Activity(int(activity_id))
        return response_for_activity(activity.json)
    except ValueError:
        return response('failed', "Activity not found", 404)      
        

@activity.errorhandler(404)
def handle_404_error(e):
    """
    Return a custom message for 404 errors.
    :param e:
    :return:
    """
    return response('failed', 'Activity resource cannot be found', 404)


@activity.errorhandler(400)
def handle_400_errors(e):
    """
    Return a custom response for 400 errors.
    :param e:
    :return:
    """
    return response('failed', 'Bad Request', 400)
