import os
from flask import Blueprint, request, abort, send_from_directory, send_file
from app import app
from app.auth.helper import token_required
from app.uploads.helper import response

# Initialize blueprint
uploads = Blueprint('uploads', __name__)

RELATIVE_UPLOAD_FOLDER = 'tmp/files'


@uploads.route('/uploads/<filename>', methods=['GET'])
@token_required
def download_file(current_user, filename):
    """
    Return all the grounds owned by the user or limit them to 10.
    Return an empty activities object if user has no buckets
    :param current_user:
    :return:
    """
    try:
        file_name = str(filename)
    except ValueError:
        return response('failed', 'Please provide a valid filename', 400)

    return send_from_directory(RELATIVE_UPLOAD_FOLDER, file_name)


@uploads.errorhandler(404)
def handle_404_error(e):
    """
    Return a custom message for 404 errors.
    :param e:
    :return:
    """
    return response('failed', 'File cannot be found', 404)


@uploads.errorhandler(400)
def handle_400_errors(e):
    """
    Return a custom response for 400 errors.
    :param e:
    :return:
    """
    return response('failed', 'Bad Request', 400)
