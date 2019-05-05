from flask import Blueprint, request, abort
from app.auth.helper import token_required
from app.team.helper import response, response_for_team, response_with_pagination, get_team_json_list, paginate_teams
from app.models import User, Team

# Initialize blueprint
team = Blueprint('team', __name__)


@team.route('/teams', methods=['GET'])
@token_required
def teams(current_user):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty activities object if user has no buckets
    :param current_user:
    :return:
    """
    user = User.get_by_id(current_user.id)
    page = request.args.get('page', 1, type=int)

    items, nex, pagination, previous = paginate_teams(page, user)

    if items:
        return response_with_pagination(get_team_json_list(items), previous, nex, pagination.total)
    return response_with_pagination([], previous, nex, 0)


@team.route('/teams/<team_id>', methods=['GET'])
@token_required
def get_team(current_user, team_id):
    """
    Return an activity object for the supplied activity id.
    :param current_user: User
    :param activity_id: Activity Id
    :return:
    """
    try:
        int(team_id)
    except ValueError:
        return response('failed', 'Please provide a valid Team Id', 400)
    else:
        team = Team.get_by_id(team_id)
        if team:
            return response_for_team(team.json())
        return response('failed', "Team not found", 404)


@team.errorhandler(404)
def handle_404_error(e):
    """
    Return a custom message for 404 errors.
    :param e:
    :return:
    """
    return response('failed', 'Team cannot be found', 404)


@team.errorhandler(400)
def handle_400_errors(e):
    """
    Return a custom response for 400 errors.
    :param e:
    :return:
    """
    return response('failed', 'Bad Request', 400)
