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
    try:
        file_name = str(filename)
    except ValueError:
        return response('failed', 'Please provide a valid filename', 400)

    return send_from_directory(RELATIVE_UPLOAD_FOLDER, file_name)


@uploads.errorhandler(404)
def handle_404_error(e):
    return response('failed', 'File cannot be found', 404)


@uploads.errorhandler(400)
def handle_400_errors(e):
    return response('failed', 'Bad Request', 400)
