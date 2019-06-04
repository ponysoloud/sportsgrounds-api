from werkzeug.utils import secure_filename
from flask import Blueprint, request, abort, url_for, redirect
from app.auth.helper import token_required
from app.user.helper import response, response_for_user, response_for_user_personal, response_for_rated_user, response_for_user_teammates, \
    get_user_json_list, get_teammates
from app.uploads.helper import upload_file, allowed_file, secure_filename
from app.models import User

# Initialize blueprint
user = Blueprint('user', __name__)


@user.route('/user', methods=['GET'])
@token_required
def get_current_user(current_user):
    user = User.get_by_id(current_user.id)
    return response_for_user_personal(user)


@user.route('/user', methods=['PUT'])
@token_required
def edit_user(current_user):
    image_name = request.json['imageName']
    image_data = request.json['image'] 

    if not image_name:
        return response('failed', 'Missing imageName attribute', 404)

    if not image_data:
        return response('failed', 'Missing image attribute', 404)

    if not allowed_file(image_name):
        return response('failed', 'Wrong image format', 400)

    print("------------ LOADING")
    
    user = User.get_by_id(current_user.id)

    try:
        secure_name = secure_filename(user, image_name)
        image_url = upload_file(secure_name, image_data)
    except ValueError:
        return response('failed', 'Wrong image format', 400)

    user.update(image_url)
    return response_for_user(user, User.get_by_id(current_user.id))


@user.route('/users/<user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
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
    try:
        int(user_id)
    except ValueError:
        return response('failed', 'Please provide a valid User Id', 400)
    else:
        user = User.get_by_id(user_id)
        count = request.args.get('count', 10, type=int)

        if user:
            items = get_teammates(user, count)

            if items:
                return response_for_user_teammates(get_user_json_list(items))
            return response_for_user_teammates([])
        return response('failed', "User not found", 404)


@user.route('/users/<user_id>/actions/rate', methods=['POST'])
@token_required
def rate_user(current_user, user_id):
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

@user.errorhandler(413)
def handle_413_errors(e):
    return response('failed', 'Uploading file is too large', 413)
