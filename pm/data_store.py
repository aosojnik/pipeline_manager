import logging

from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

class DataStore:
    def __init__(self, collection_name, connection_url):
        self.client = MongoClient(connection_url)
        self.db = self.client.get_database()
        self.collection = self.db[collection_name]
        self.archive_collection = None
        archive_collection_name = f"{collection_name}-{datetime.utcnow().year}-{datetime.utcnow().month - 1}"
        if archive_collection_name in self.db.list_collection_names():
            self.archive_collection = self.db[archive_collection_name]


    def insert_one(self, data):
        result = self.collection.insert_one(data)
        return result.inserted_id

    def insert_many(self, data):
        result = self.collection.insert_many(data)
        return result.inserted_ids

    def find_by_id(self, document_id):
        result = self.collection.find_one({ '_id': ObjectId(document_id) })
        return result

    def update_one(self, filter, update):
        result = self.collection.update_one(filter, update)
        return result

    def replace_one(self, filter, replacement):
        result = self.collection.replace_one(filter, replacement)
        return result

class SensorsDataStore(DataStore):
    def __init__(self, collection_name, connection_url):
        super().__init__(collection_name, connection_url)

    def find_by_location(self, location_id):
        result = self.collection.find_one({ 'LocationId': location_id })
        return result

    def get_sensor_data(self, from_timestamp, to_timestamp, location_id, source_id = None, limit = 9000):
        query = {
            'LocationId': location_id,
            'Data.Timestamp': {
                '$gt': from_timestamp,
                '$lte': to_timestamp
            }
        }

        if source_id is not None:
            query['SourceId'] = source_id
        
        logging.debug(f"Loading from {self.collection.name}")
        result = list(self.collection.find(query, limit=limit))
        logging.debug(f"Loaded {len(result)} from collection")
        
        if self.archive_collection is not None:
            result.extend(list(self.archive_collection.find(query, limit=limit)))
            logging.debug(f"Total {len(result)} results loaded")
        return result
