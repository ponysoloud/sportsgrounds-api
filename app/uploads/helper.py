import os
from hashlib import md5
from base64 import decodebytes, b64decode
from flask import make_response, jsonify, url_for
from app import app, db, s3
from app.models import User

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg'])
BUCKET_NAME = os.getenv('BUCKETEER_BUCKET_NAME')

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

def upload_file(filename, filedata):
    bin_data = b64decode(filedata)

    try:
        s3.put_object(ACL='public-read', Body=bin_data, Bucket=BUCKET_NAME, Key=filename)
    except Exception as e:
        raise ValueError(e)

    file_url = 'https://%s.s3.amazonaws.com/%s' % (BUCKET_NAME, filename)
    return file_url