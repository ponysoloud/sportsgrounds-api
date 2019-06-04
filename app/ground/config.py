import os

class SourceConfig(object):
    GROUNDS_SOURCE_BASE_URL = 'https://apidata.mos.ru'
    GROUNDS_SOURCE_API_KEY = os.getenv('SOURCE_SPORTGROUNDS_DATASET_API_KEY')
    GROUNDS_SOURCE_MAX_COUNT_ROWS = 500
    GROUNDS_SOURCE_DATASETS_IDS = {
        'football_pitches_dataset': 886,
        'sports_grounds_dataset': 893,
        'outdoor_training_grounds_dataset': 898
    }
