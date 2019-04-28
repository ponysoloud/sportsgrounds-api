from enum import Enum
from app.models import Activity

class ActivitiesEnum(Enum):
    easy_training = 1
    football = 2
    hockey = 3
    basketball = 4
    skating = 5
    ice_skating = 6
    workout = 7
    yoga = 8
    box = 9

    @property
    def description(self):
        if self is ActivitiesEnum.easy_training:
            return ''
        if self is ActivitiesEnum.football:
            return ''
        if self is ActivitiesEnum.hockey:
            return ''
        if self is ActivitiesEnum.basketball:
            return ''
        if self is ActivitiesEnum.skating:
            return ''
        if self is ActivitiesEnum.ice_skating:
            return ''
        if self is ActivitiesEnum.workout:
            return ''
        if self is ActivitiesEnum.yoga:
            return ''
        if self is ActivitiesEnum.box:
            return ''

    @property
    def persistent(self):
        return Activity.get_by_id(self.value)

class SourceGround(object):

    def __init__(self, id, name, nameWinter, district, address, website, hasMusic, hasWifi, hasToilet, hasEatery, hasDressingRoom, hasLighting, paid, surface, latitude, longitude):
        self.id = id
        self.name = name
        self.nameWinter = nameWinter
        self.district = district
        self.address = address
        self.website = website
        self.hasMusic = hasMusic
        self.hasWifi = hasWifi
        self.hasToilet = hasToilet
        self.hasEatery = hasEatery
        self.hasDressingRoom = hasDressingRoom
        self.hasLighting = hasLighting
        self.paid = paid
        self.surface = surface
        self.latitude = latitude
        self.longitude = longitude
        self.activities = []

    @classmethod
    def encodeFromJSON(cls, json):
        try:
            cells = json['Cells']

            id = cells['global_id']
            name = cells['ObjectName']
            nameWinter = cells.get('NameWinter', None)
            district = cells['District']
            address = cells['Address']
            website = cells.get('WebSite', None)

            hasMusic = cells.get('HasMusic', 'нет') == 'да'
            hasWifi = cells.get('HasWifi', 'нет') == 'да'
            hasToilet = cells.get('HasToilet', 'нет') == 'да'
            hasEatery = cells.get('HasEatery', 'нет') == 'да'
            hasDressingRoom = cells.get('HasDressingRoom', 'нет') == 'да'

            hasLighting = cells.get('Lighting', 'без дополнительного освещения')  != 'без дополнительного освещения'

            paid = cells.get('Paid', 'бесплатно') == 'платно'
            surface = cells.get('SurfaceTypeWinter', None)

            geoData = cells['geoData']
            coordinates = geoData['coordinates']

            longitude = coordinates[0]
            latitude = coordinates[1]

            return cls(id, name, nameWinter, district, address, website, hasMusic, hasWifi, hasToilet, hasEatery, hasDressingRoom, hasLighting, paid, surface, latitude, longitude)
        except KeyError:
            return None