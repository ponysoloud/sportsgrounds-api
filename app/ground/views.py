from flask import Blueprint, request, abort
from app.auth.helper import token_required
from app.ground.helper import begin_updating_grounds_dataset_sheduled

# Initialize blueprint
ground = Blueprint('ground', __name__)

@ground.record
def record(state):
    begin_updating_grounds_dataset_sheduled(state)

    