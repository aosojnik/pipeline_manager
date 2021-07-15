from .data_store import SensorsDataStore

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'PipelineManager'))
from .readers import Reader
from .writers import Writer

SENSORS_COLLECTION_NAME='SensorDataPackages'
COACHING_ADDITIONAL_DATA_SOURCES_COLLECTION_NAME='CoachingAdditionalDataSources'

def is_coaching_other_source(source_id):
    return not source_id.startswith('sens_')

class MongoReader(Reader):
    def __init__(self, location_id, connection_url):
        super().__init__(location_id)
        self.sensors_data_datastore = SensorsDataStore(SENSORS_COLLECTION_NAME, connection_url)
        self.additional_data_datastore = SensorsDataStore(COACHING_ADDITIONAL_DATA_SOURCES_COLLECTION_NAME, connection_url)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sensors_data_datastore.client.close()
        self.additional_data_datastore.client.close()

    def query(self, source_id, start_time, end_time):
        # for mongo convert to milliseconds
        from_timestamp = start_time * 1000
        to_timestamp = end_time * 1000

        data = []
        if is_coaching_other_source(source_id):
            data = self.additional_data_datastore.get_sensor_data(from_timestamp, to_timestamp, self.location_id, source_id)
        else:
            data = self.sensors_data_datastore.get_sensor_data(from_timestamp, to_timestamp, self.location_id, source_id)

        for data_point in data:
            timestamp, source_id = data_point['Data']['Timestamp'] / 1000, data_point['SourceId'] # Data points in DB are stored with millisecond resolution
            timestep = data_point['Data']['Timestep']
            if source_id not in self._DATA:
                self._DATA[source_id] = {}
            measurements = data_point['Data']['Measurements']
            measurement_timestep = timestep / len(measurements)
            for i, measurement in enumerate(measurements):
                m_timestamp = timestamp + measurement_timestep * i
                self._DATA[source_id][m_timestamp] = (m_timestamp, measurement_timestep, measurement)

class InvalidOtherSourceError(Exception):
    def __init__(self, other_source_id):
        self.other_source_id = other_source_id
    def __str__(self):
        return "Invalid other source id: " + self.other_source_id
    pass

class MongoWriter(Writer):
    def __init__(self, location_id, connection_url):
        super().__init__(location_id)
        self.additional_data_datastore = SensorsDataStore(COACHING_ADDITIONAL_DATA_SOURCES_COLLECTION_NAME, connection_url)

    def make_dict(self, source_id, timestamp, timestep, value):
        o = {
            'SourceId': source_id,
            'LocationId': self.location_id,
            'Data': {
                'Timestamp': int(timestamp) * 1000,
                'Timestep': int(timestep),
                'Measurements': [value]
            }
        }
        return o

    def __exit__(self, exc_type, exc_val, ext_tb):
        dicts = []
        for source_id in self._DATA:
            if not is_coaching_other_source(source_id):
                raise InvalidOtherSourceError(source_id)

            for timestamp, (timestamp, timespan, value) in self._DATA[source_id].items():
                dicts.append(self.make_dict(source_id, timestamp, timespan, value))

        if dicts:
            self.additional_data_datastore.insert_many(dicts)
