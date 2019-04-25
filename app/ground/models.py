
class SourceGround(object):

    def __init__(self, identifier, name, nameWinter, district, address, website, hasMusic, hasWifi, hasToilet, hasEatery, hasDressingRoom, paid, surface, latitude, longitude):
        self.identifier = identifier
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
        self.paid = paid
        self.surface = surface
        self.latitude = latitude
        self.longitude = longitude
        self.activities = []

    @classmethod
    def encodeFromJSON(cls, json):
        try:
            cells = json['Cells']

            global_id = cells['global_id']
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
            surface = cells.get('SurfaceTypeWinter', '')

            geoData = cells['geoData']
            coordinates = geoData['coordinates']

            longitude = coordinates[0]
            latitude = coordinates[1]

            return cls(global_id, name, nameWinter, district, address, website, hasMusic, hasWifi, hasToilet, hasEatery, hasDressingRoom, paid, surface, latitude, longitude)
        except KeyError:
            return None