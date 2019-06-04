import os
import requests
from flask import make_response, jsonify, url_for
from flask_sqlalchemy import BaseQuery
from sqlalchemy import func, or_
from sqlalchemy.orm import aliased
from app import app, db
from app.models import User, Team

def response(status, message, code):
    return make_response(jsonify({
        'status': status,
        'message': message
    })), code


def response_for_user(user, other_user=None):
    return make_response(jsonify({
        'status': 'success',
        'user': user.json(other_user)
    }))


def response_for_user_personal(user):
    return make_response(jsonify({
        'status': 'success',
        'user': user.personal_json()
    }))


def response_for_rated_user(user, by_user, status_code):
    return make_response(jsonify({
        'status': 'success',
        'user': user.json(by_user)
    })), status_code


def get_user_json_list(users):
    json_list = []
    for user in users:
        json_list.append(user.json())
    return json_list


def response_for_user_teammates(users):
    return make_response(jsonify({
        'status': 'success',
        'users': users
    })), 200


def get_teammates(user, count):
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