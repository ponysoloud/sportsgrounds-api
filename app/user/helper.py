import os
import requests
from flask import make_response, jsonify
from app import app
from app.models import User

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

def response_for_user(user, other_user=None):
    """
    Return the response for when a single bucket when requested by the user.
    :param user_bucket:
    :return:
    """
    return make_response(jsonify({
        'status': 'success',
        'user': user.json(other_user)
    }))

def response_for_user_personal(user):
    """
    Return the response for when a single bucket when requested by the user.
    :param user_bucket:
    :return:
    """
    return make_response(jsonify({
        'status': 'success',
        'user': user.personaljson()
    }))

def response_for_rated_user(user, by_user, status_code):
    """
    Method returning the response when a bucket has been successfully created.
    :param status_code:
    :param user_bucket: Bucket
    :return: Http Response
    """
    return make_response(jsonify({
        'status': 'success',
        'event': user.json(by_user)
    })), status_code