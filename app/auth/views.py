from app import bcrypt
from flask import Blueprint, request
from flask.views import MethodView
from app.models import User, BlackListToken
from app.auth.helper import response, response_auth
from sqlalchemy import exc
from app.auth.helper import token_required
from dateutil.parser import isoparse
import re

auth = Blueprint('auth', __name__)


class RegisterUser(MethodView):
    def post(self):
        """
        Register a user, generate their token and add them to the database
        :return: Json Response with the user`s token
        """
        if request.content_type == 'application/json':
            post_data = request.get_json()
            email = post_data.get('email')
            password = post_data.get('password')

            name = post_data.get('name')
            surname = post_data.get('surname')

            birthday_value = post_data.get('birthday')

            if not email:
                return response('failed', 'Missing email attribute', 400)

            if not password:
                return response('failed', 'Missing password attribute', 400)

            if not name:
                return response('failed', 'Missing name attribute', 400)

            if not surname:
                return response('failed', 'Missing surname attribute', 400)

            if not birthday_value:
                return response('failed', 'Missing birthday attribute', 400)

            try:
                birthday = isoparse(str(birthday_value))
            except ValueError:
                return response('failed', 'Wrong birthday attribute type', 400)

            if re.match(r"[^@]+@[^@]+\.[^@]+", email) and len(password) > 4:
                user = User.get_by_email(email)
                if not user:
                    token = User(email, password, name, surname, birthday).save()
                    return response_auth('success', token, 201)
                else:
                    return response('failed', 'Failed, User already exists, Please sign In', 400)
            return response('failed', 'Missing or wrong email format or password is less than four characters', 400)
        return response('failed', 'Content-type must be json', 400)


class LoginUser(MethodView):
    def post(self):
        """
        Login a user if the supplied credentials are correct.
        :return: Http Json response
        """
        if request.content_type == 'application/json':
            post_data = request.get_json()
            email = post_data.get('email')
            password = post_data.get('password')
            if re.match(r"[^@]+@[^@]+\.[^@]+", email) and len(password) > 4:
                user = User.query.filter_by(email=email).first()
                if not user:
                    return response('failed', 'User does not exist', 401)
                if user and bcrypt.check_password_hash(user.password, password):
                    return response_auth('success', user.encode_auth_token(user.id), 200)
                return response('failed', 'Password is incorrect', 400)
            return response('failed', 'Missing or wrong email format or password is less than four characters', 401)
        return response('failed', 'Content-type must be json', 202)


class LogoutUser(MethodView):
    """
    Class to log out a user
    """
    def post(self):
        """
        Try to logout a user using a token
        :return:
        """
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                auth_token = auth_header.split(" ")[1]
            except IndexError:
                return response('failed', 'Provide a valid auth token', 403)
            else:
                decoded_token_response = User.decode_auth_token(auth_token)
                if not isinstance(decoded_token_response, str):
                    token = BlackListToken(auth_token)
                    token.blacklist()
                    return response('success', 'Successfully logged out', 200)
                return response('failed', decoded_token_response, 401)
        return response('failed', 'Provide an authorization header', 403)


@auth.route('/auth/reset/password', methods=['POST'])
@token_required
def reset_password(current_user):
    if request.content_type == "application/json":
        data = request.get_json()
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')
        password_confirmation = data.get('passwordConfirmation')
        if not old_password or not new_password or not password_confirmation:
            return response('failed', "Missing required attributes", 400)
        if bcrypt.check_password_hash(current_user.password, old_password.encode('utf-8')):
            if not new_password == password_confirmation:
                return response('failed', 'New Passwords do not match', 400)
            if not len(new_password) > 4:
                return response('failed', 'New password should be greater than four characters long', 400)
            current_user.reset_password(new_password)
            return response('success', 'Password reset successfully', 200)
        return response('failed', "Incorrect password", 401)
    return response('failed', 'Content type must be json', 400)


@auth.route('/auth/refresh', methods=['POST'])
@token_required
def refresh_token(current_user):
    return response_auth('success', current_user.encode_auth_token(current_user.id), 200)


# Register classes as views
registration_view = RegisterUser.as_view('register')
login_view = LoginUser.as_view('login')
logout_view = LogoutUser.as_view('logout')

# Add rules for the api Endpoints
auth.add_url_rule('/auth/register', view_func=registration_view, methods=['POST'])
auth.add_url_rule('/auth/login', view_func=login_view, methods=['POST'])
auth.add_url_rule('/auth/logout', view_func=logout_view, methods=['POST'])
