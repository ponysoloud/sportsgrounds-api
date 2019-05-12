import os
from hashlib import md5
from base64 import decodebytes
from flask import make_response, jsonify, url_for
from app import app, db
from app.models import User

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg'])

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

def allowed_file(filename):
    return (not file_extension(filename) is None) and (file_extension(filename) in ALLOWED_EXTENSIONS)

def file_extension(filename):
    if not '.' in filename:
        return None

    return filename.rsplit('.', 1)[1].lower()

def secure_filename(user, filename):
    exten = file_extension(filename)
    if not exten:
        raise ValueError('Wrong format of filename')

    user_identifier = ''.join([user.name, user.surname, str(user.id)])
    extension = '.' + exten
    secure_filename = md5(user_identifier.encode()).hexdigest() + extension

    return secure_filename

def upload_file(filename, file):
    files_directory = app.config['UPLOAD_FOLDER']
    filepath = os.path.join(files_directory, filename)

    file.save(filepath)

    file_url = os.path.join('/uploads', filename)
    return file_url