import os
import requests
from datetime import datetime, date
from flask import make_response, jsonify, url_for
from app import app, app_sheduler, db
from app.models import ActivitiesEnum, Activity, Ground
from app.ground.models import SourceGround
from app.ground.config import SourceConfig

UPDATE_GROUNDS_DATASET_TIME_DAYS = 1
UPDATE_GROUNDS_DATASET_JOB_ID = 'app.ground.helper.update_grounds_dataset'

def begin_sheduled_updating_grounds_dataset(state):
    print('app.ground.helper.begin_sheduled_updating_grounds_dataset')
    app_sheduler.add_job(func=update_grounds_dataset, trigger='interval', days=UPDATE_GROUNDS_DATASET_TIME_DAYS, id=UPDATE_GROUNDS_DATASET_JOB_ID, coalesce=True)

def update_grounds_dataset():
    print('app.ground.helper.update_grounds_dataset')
    source_config = SourceConfig()

    base_url = source_config.GROUNDS_SOURCE_BASE_URL
    api_key = source_config.GROUNDS_SOURCE_API_KEY
    dataset_max_count_rows = source_config.GROUNDS_SOURCE_MAX_COUNT_ROWS

    try:
        #Receive version of Grounds Source API
        api_version = int(get_grounds_source_api_version(base_url + '/version'))

        #Receive all datasets from Grounds Source API
        sources = []

        for k in source_config.GROUNDS_SOURCE_DATASETS_IDS.keys():
            dataset_id = source_config.GROUNDS_SOURCE_DATASETS_IDS[k]
            dataset_url = base_url + '/v' + str(api_version) + '/datasets/' + str(dataset_id)

            #Receive rows count of k dataset
            dataset_rows_count = int(get_grounds_source_dataset_rows_count(dataset_url, api_key))

            dataset_rows = []
            dataset_rows_remains = dataset_rows_count
            while dataset_rows_remains > 0:
                dataset_rows_skip = dataset_rows_count - dataset_rows_remains
                dataset_rows_top = min(dataset_rows_remains, dataset_max_count_rows)

                dataset_rows_part = get_grounds_source_dataset_rows(dataset_url + '/rows', api_key, dataset_rows_top, dataset_rows_skip, k)
                dataset_rows.extend(dataset_rows_part)

                dataset_rows_remains -= dataset_rows_top

            sources.extend(dataset_rows)

            print('dataset loaded -', k)
            print('count -', len(dataset_rows))

        print('source loaded')

        #Update local database
        for g in sources:
            persistent_ground = Ground.get_by_source_id(g.id)

            if persistent_ground:
                persistent_ground.name = g.name
                persistent_ground.district = g.district
                persistent_ground.address = g.address
                persistent_ground.website = g.website
                persistent_ground.hasMusic = g.hasMusic
                persistent_ground.hasWifi = g.hasWifi
                persistent_ground.hasToilet = g.hasToilet
                persistent_ground.hasEatery = g.hasEatery
                persistent_ground.hasDressingRoom = g.hasDressingRoom
                persistent_ground.hasLighting = g.hasLighting
                persistent_ground.paid = g.paid

                persistent_ground.activities = list(map(lambda a: a.persistent, g.activities))
            else:
                ground = Ground(g.id, g.name, g.district, g.address, g.website, g.hasMusic, g.hasWifi, g.hasToilet, g.hasEatery, g.hasDressingRoom, g.hasLighting, g.paid, g.latitude, g.longitude)
                ground.activities = list(map(lambda a: a.persistent, g.activities))
                db.session.add(ground)
        
        db.session.commit()

    except ValueError as error:
        print(error)

def get_grounds_source_api_version(url):
    api_version = requests.get(url).json().get("Version", None)

    if api_version is None:
        raise ValueError('Grounds Source API responsed bad version')
    else:
        return api_version

def get_grounds_source_dataset_rows_count(url, api_key):
    rows_count = requests.get(url, params = {'api_key': api_key}).json().get('ItemsCount', None)

    if rows_count is None:
        raise ValueError('Grounds Source API responsed bad dataset passport')
    else:
        return rows_count

def get_grounds_source_dataset_rows(url, api_key, top, skip, source_dataset_name):
    dataset_rows = requests.get(url, params = {'api_key': api_key, '$top': top, '$skip':skip}).json()

    grounds_source_dataset_rows = []
    for row in dataset_rows:
        source_ground = SourceGround.encodeFromJSON(row)
        if source_ground:
            define_ground_activity(source_ground, source_dataset_name)
            grounds_source_dataset_rows.append(source_ground)

    return grounds_source_dataset_rows

def isWinter():
    winter_ranges = [(date(2000, 1, 1), date(2000, 3, 31)), (date(2000, 12, 1), date(2000, 12, 31))]
    today = datetime.utcnow().date().replace(year=2000)

    for start, end in winter_ranges:
        if start <= today <= end:
            return True

    return False

def define_ground_activity(source_ground, source_dataset_name):
    if source_dataset_name == 'football_pitches_dataset':
        source_ground.activities.append(ActivitiesEnum.football)
    elif source_dataset_name == 'outdoor_training_grounds_dataset':
        source_ground.activities.append(ActivitiesEnum.workout)
    elif source_dataset_name == 'sports_grounds_dataset':
        today_is_winter = isWinter()

        ground_type = source_ground.nameWinter

        if ground_type is None:
            ground_type = 'универсальная'

        ground_surface = source_ground.surface

        if ground_surface is None:
            ground_surface = 'бетон'

        isIceRink = 'каток' in ground_type
        isBasketball = 'баскетбол' in ground_type
        isFootball = 'футбол' in ground_type
        isUniversal = 'универс' in ground_type.lower()

        isSolidSurface = ('асфальт' in ground_surface) or ('бетон' in ground_surface) or ('лед' in ground_surface)
        isSoilSurface = 'грунт' in ground_surface
        isSoftSurface = not isSolidSurface and not isSoilSurface
        
        activities = set()
        if today_is_winter:
            if isIceRink:
                activities.update([ActivitiesEnum.ice_skating, ActivitiesEnum.hockey])

            if isBasketball and not isIceRink:
                activities.add(ActivitiesEnum.easy_training)

            if not isBasketball and not isIceRink:
                activities.update([ActivitiesEnum.football, ActivitiesEnum.easy_training])
        else:
            if isBasketball:
                activities.add(ActivitiesEnum.basketball)

            if isFootball:
                activities.add(ActivitiesEnum.football)

            if isUniversal:
                if isSolidSurface:
                    activities.add(ActivitiesEnum.skating)
                elif isSoilSurface:
                    activities.add(ActivitiesEnum.football)
                elif isSoftSurface:
                    activities.update([ActivitiesEnum.easy_training, ActivitiesEnum.yoga, ActivitiesEnum.box, ActivitiesEnum.football, ActivitiesEnum.basketball])

        source_ground.activities = list(activities)
