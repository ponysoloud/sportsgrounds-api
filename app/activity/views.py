from flask import Blueprint, request, abort
from app.auth.helper import token_required
from app.activity.helper import response, response_for_activity, response_for_activities, get_activity_json_list
from app.models import Activity

# Initialize blueprint
activity = Blueprint('activity', __name__)


@activity.route('/activities/', methods=['GET'])
@token_required
def activities(current_user):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty buckets object if user has no buckets
    :param current_user:
    :return:
    """
    activities = Activity.query.all()
    if not activities:
        activities = []
    return response_for_activities(get_activity_json_list(activities))


@activity.route('/activities/<activity_id>', methods=['GET'])
@token_required
def get_activity(current_user, activity_id):
    """
    Return a user bucket with the supplied user Id.
    :param current_user: User
    :param bucket_id: Bucket Id
    :return:
    """
    try:
        int(activity_id)
    except ValueError:
        return response('failed', 'Please provide a valid Activity Id', 400)
    else:
        activity = Activity.get_by_id(activity_id)
        if activity:
            return response_for_activity(activity.json())
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
