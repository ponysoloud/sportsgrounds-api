from flask import make_response, jsonify, url_for
from app import app
from app.models import Activity

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

def response_for_activity(activity):
    """
    Return the response for when a single bucket when requested by the user.
    :param activity:
    :return:
    """
    return make_response(jsonify({
        'status': 'success',
        'activity': activity
    }))

def response_for_activities(activities):
    """
    Return the response for when a single bucket when requested by the user.
    :param user_bucket:
    :return:
    """
    return make_response(jsonify({
        'status': 'success',
        'activities': activities
    }))

def get_activity_json_list(activities):
    """
    Make json objects of given activities and add them to a list.
    :param user_buckets: Bucket
    :return:
    """
    json_list = []
    for activity in activities:
        json_list.append(activity.json)
    return json_list
