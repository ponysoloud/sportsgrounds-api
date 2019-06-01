import os
import requests
from flask import make_response, jsonify, url_for
from flask_sqlalchemy import BaseQuery
from sqlalchemy import func, or_
from sqlalchemy.orm import aliased
from app import app, db
from app.models import User, Team

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
        'user': user.personal_json()
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
        'user': user.json(by_user)
    })), status_code


def get_user_json_list(users):
    """
    Make json objects of the grounds and add them to a list.
    :param user_buckets: Bucket
    :return:
    """
    json_list = []
    for user in users:
        json_list.append(user.json())
    return json_list


def response_for_user_teammates(users):
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
        'users': users
    })), 200


def get_teammates(user, count):
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

    target = aliased(User)
    teammate = aliased(User)
    ta_team = aliased(Team)
    te_team = aliased(Team)
    teammates_query = db.session.query(target, teammate, func.count(teammate.id)) \
        .join((ta_team, target.teams)) \
        .join((te_team, teammate.teams)) \
        .filter(ta_team.id == te_team.id) \
        .filter(target.id != teammate.id) \
        .filter(target.id == user.id) \
        .group_by(target.id, teammate.id) \
        .order_by(func.count(teammate.id).desc()) \
        .limit(count)

    items = list(map(lambda i: i[1], teammates_query.all()))
    return items