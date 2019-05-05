from flask import make_response, jsonify, url_for
from app import app, db
from app.models import Event, Team, User

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

def response_for_team(team):
    """
    Return the response for when a single bucket when requested by the user.
    :param activity:
    :return:
    """
    return make_response(jsonify({
        'status': 'success',
        'team': team
    }))

def get_team_json_list(teams):
    """
    Make json objects of given activities and add them to a list.
    :param user_buckets: Bucket
    :return:
    """
    json_list = []
    for team in teams:
        json_list.append(team.json())
    return json_list

def response_with_pagination(teams, previous, nex, count):
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
        'previous': previous,
        'next': nex,
        'count': count,
        'teams': teams
    })), 200


def paginate_teams(page, user):
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
