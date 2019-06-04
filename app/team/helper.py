from flask import make_response, jsonify, url_for
from app import app, db
from app.models import Event, Team, User

def response(status, message, code):
    return make_response(jsonify({
        'status': status,
        'message': message
    })), code

def response_for_team(team):
    return make_response(jsonify({
        'status': 'success',
        'team': team
    }))

def get_team_json_list(teams):
    json_list = []
    for team in teams:
        json_list.append(team.json())
    return json_list

def response_with_pagination(teams, previous, nex, count):
    return make_response(jsonify({
        'status': 'success',
        'previous': previous,
        'next': nex,
        'count': count,
        'teams': teams
    })), 200


def paginate_teams(page, user):
    pagination = Team.query.join(User, Team.participants).filter(User.id==user.id).order_by(Team.create_at.desc()) \
        .paginate(page=page, per_page=app.config['TEAMS_PER_PAGE'], error_out=False)

    previous = None
    if pagination.has_prev:
        previous = url_for('team.teams', page=page - 1, _external=True)

    nex = None
    if pagination.has_next:
        nex = url_for('team.teams', page=page + 1, _external=True)

    items = pagination.items

    return items, nex, pagination, previous
