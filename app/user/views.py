from flask import Blueprint, request, abort
from app.auth.helper import token_required
from app.user.helper import response, response_for_user, response_for_user_personal, response_for_rated_user, response_with_pagination_teammates, \
    get_user_json_list, paginate_teammates
from app.models import User

# Initialize blueprint
user = Blueprint('user', __name__)

@user.route('/user', methods=['GET'])
@token_required
def get_current_user(current_user):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty Grounds object if user has no grounds
    :param current_user:
    :return:
    """

    user = User.get_by_id(current_user.id)
    return response_for_user_personal(user)


@user.route('/users/<user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty Grounds object if user has no grounds
    :param current_user:
    :return:
    """
    try:
        int(user_id)
    except ValueError:
        return response('failed', 'Please provide a valid User Id', 400)
    else:
        user = User.get_by_id(user_id)
        if user:
            if user.id == current_user.id:
                return response_for_user_personal(user)
            else:
                return response_for_user(user, User.get_by_id(current_user.id))
        return response('failed', "User not found", 404)


@user.route('/users/<user_id>/teammates', methods=['GET'])
@token_required
def get_user_teammates(current_user, user_id):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty Grounds object if user has no grounds
    :param current_user:
    :return:
    """
    try:
        int(user_id)
    except ValueError:
        return response('failed', 'Please provide a valid User Id', 400)
    else:
        user = User.get_by_id(user_id)
        page = request.args.get('page', 1, type=int)

        if user:
            items, nex, pagination, previous = paginate_teammates(page, user)

            if items:
                return response_with_pagination_teammates(get_user_json_list(items), previous, nex, pagination.total)
            return response_with_pagination_teammates([], previous, nex, 0)
        return response('failed', "User not found", 404)


@user.route('/users/<user_id>/actions/rate', methods=['POST'])
@token_required
def rate_user(current_user, user_id):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty Grounds object if user has no grounds
    :param current_user:
    :return:
    """
    try:
        int(user_id)
    except ValueError:
        return response('failed', 'Please provide a valid User Id', 400)
    else:
        if int(user_id )== current_user.id:
            return response('failed', 'User can\'t rate yourself', 400)

        user_to_rate = User.get_by_id(user_id)
        if not user_to_rate:
            return response('failed', "User not found", 404)

        user = User.get_by_id(current_user.id)
        if user_to_rate.rated_by_user(user):
            return response('failed', 'User already rated', 400)

        user_to_rate.rated_me_users.append(user)
        user_to_rate.update()
        return response_for_rated_user(user_to_rate, user, 201)
        

@user.route('/users/<user_id>/actions/unrate', methods=['POST'])
@token_required
def unrate_user(current_user, user_id):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty Grounds object if user has no grounds
    :param current_user:
    :return:
    """
    try:
        int(user_id)
    except ValueError:
        return response('failed', 'Please provide a valid User Id', 400)
    else:
        if int(user_id) == current_user.id:
            return response('failed', 'User can\'t unrate yourself', 400)

        user_to_unrate = User.get_by_id(user_id)
        if not user_to_unrate:
            return response('failed', "User not found", 404)

        user = User.get_by_id(current_user.id)
        if not user_to_unrate.rated_by_user(user):
            return response('failed', 'User not rated to be unrated', 400)

        user_to_unrate.rated_me_users.remove(user)
        user_to_unrate.update()
        return response_for_rated_user(user_to_unrate, user, 201)


@user.errorhandler(404)
def handle_404_error(e):
    """
    Return a custom message for 404 errors.
    :param e:
    :return:
    """
    return response('failed', 'User cannot be found', 404)


@user.errorhandler(400)
def handle_400_errors(e):
    """
    Return a custom response for 400 errors.
    :param e:
    :return:
    """
    return response('failed', 'Bad Request', 400)
