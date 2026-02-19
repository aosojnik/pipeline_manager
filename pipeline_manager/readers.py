import csv, json, http.client, os.path
from urllib.parse import urlencode

from .utils import f_timestamp

class Reader():
    def __init__(self):
        self._DATA = {}

    def __str__(self):
        return self.__class__.__name__

    def set_logger(self, logger):
        self._LOGGER = logger

    def log(self, msg, level):
        self._LOGGER.print(f"[{self}] {msg}", level)

    def load(self):
        pass

    def __getitem__(self, item):
        source_id, target_time = item
        if source_id in self._DATA:
            if isinstance(target_time, slice):
                start = target_time.start
                end = target_time.stop
                return sorted([val for time, val in self._DATA[source_id].items() if start < time <= end])
            else:
                return [ self._DATA[source_id][target_time] ]
        else:
            return []

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __contains__(self, item):
        source_id, timestamp = item
        return source_id in self._DATA and timestamp in self._DATA[source_id]

    def query(self, source_id, start_time, end_time):
        raise NotImplementedError("The reader is missing the query method.")

    def is_online(self):
        return True

    def add_entries(self, source_id, entries):
        if source_id not in self._DATA:
            self._DATA[source_id] = {}
        for entry in entries:
            timestamp = entry[0]
            self._DATA[source_id][timestamp] = entry

class CSVReader(Reader):

    def __init__(self, location_id, targets):
        super().__init__(location_id)
        self.targets = targets

        import sys
        csv.field_size_limit(sys.maxsize)

    def is_online(self):
        return False

    def load(self):
        for filename, timestep in self.targets:
            
            with open(filename) as f:
                reader = csv.reader(f)
                header = next(reader)
                for source_id in header[1:]:
                    if source_id not in self._DATA:
                        self._DATA[source_id] = {}
                for row in reader:
                    timestamp, *data = row
                    timestamp = int(timestamp) / 1000
                    for i, value in enumerate(data):
                        source_id = header[i+1]
                        try:
                            true_val = eval(value)
                        except Exception:
                            true_val = value
                        finally:
                            self._DATA[source_id][timestamp] = (timestamp, timestep, true_val)

    def query(self, source_id, start_time, end_time):
        pass

class JSONReader__SAAM(Reader):
    def __init__(self, location_id, targets):
        super().__init__()
        self.location_id = location_id
        self.targets = targets

    def is_online(self):
        return False

    def load(self):
        for filename in self.targets:
            
            with open(filename) as f:
                _ = f.read().replace('\x13', '')
                data = json.loads(_)
            for data_point in data:
                if self.location_id == data_point['LocationId']:
                    timestamp, source_id = data_point['Data']['Timestamp'] / 1000, data_point['SourceId'] # Data points in DB are stored with millisecond resolution
                    timestep = data_point['Data']['Timestep']
                    if source_id not in self._DATA:
                        self._DATA[source_id] = {}
                    measurements = data_point['Data']['Measurements']
                    measurement_timestep = timestep / len(measurements)
                    for i, measurement in enumerate(measurements):
                        m_timestamp = timestamp + measurement_timestep * i
                        self._DATA[source_id][m_timestamp] = (m_timestamp, measurement_timestep, measurement)

    def query(self, source_id, start_time, end_time):
        pass

class JSONReader(Reader):
    def __init__(self, location_id, targets):
        super().__init__()
        self.location_id = location_id
        self.targets = targets

    def is_online(self):
        return False

    def load(self):
        for filename in self.targets:
            
            with open(filename) as f:
                _ = f.read().replace('\x13', '')
                data = json.loads(_)
            for data_point in data:
                if self.location_id == data_point['location_id'] or data_point['location_id'] == '':
                    timestamp, source_id = data_point['timestamp'], data_point['source_id']
                    timestep = data_point['timestep']
                    if source_id not in self._DATA:
                        self._DATA[source_id] = {}
                    measurements = data_point['values']
                    measurement_timestep = timestep / len(measurements)
                    for i, measurement in enumerate(measurements):
                        m_timestamp = timestamp + measurement_timestep * i
                        self._DATA[source_id][m_timestamp] = (m_timestamp, measurement_timestep, measurement)

    def query(self, source_id, start_time, end_time):
        pass


class HTTPReader(Reader):
    def __init__(self, location_id, connection_settings):
        super().__init__()
        self.location_id = location_id
        self.settings = connection_settings

    def load(self):
        if self.settings['protocol'] == 'HTTPS':
            self.sensor_connection = None
            self.other_connection = None
            pass
        else:
            raise NotImplementedError('Protocol not yet implemented: ' + self.settings['protocol'])

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sensor_connection:
            self.sensor_connection.close()
        if self.other_connection:
            self.other_connection.close()

    def query(self, source_id, start_time, end_time):
        time_format = self.settings['time_format']
        time = start_time
        if source_id[:5] == "sens_":
            while time + 21600 < end_time:
                self.query(source_id, time, time + 21600)
                time += 21600
        params = {'StartDate': f_timestamp(time), 'EndDate': f_timestamp(end_time)}

        if source_id[:5] == "sens_":
            self.sensor_connection = http.client.HTTPSConnection(self.settings['sensor_server'])
            url = "/" + self.settings['sensor_query_url'].format(location_id=self.location_id, source_id=source_id) + "?" + urlencode(params)

            self.log(f"Querying sensor {url}", 4)
            self.sensor_connection.request('GET', url)
        
            response = self.sensor_connection.getresponse()
        else:
            self.other_connection = http.client.HTTPSConnection(self.settings['other_server'])
            params['SourceId'] = source_id
            url = "/" + self.settings['other_query_url'].format(location_id=self.location_id, source_id=source_id) + "?" + urlencode(params)

            self.log(f"Querying other {url}", 4)
            self.other_connection.request('GET', url)
        
            response = self.other_connection.getresponse()

        if response.status == 200:
            r_data = response.read()
            data = json.loads(r_data)
            for data_point in data:
                timestamp, source_id = data_point['data']['timestamp'] / 1000, data_point['sourceId'] # Data points in DB are stored with millisecond resolution
                timestep = data_point['data']['timestep']
                if source_id not in self._DATA:
                    self._DATA[source_id] = {}
                measurements = data_point['data']['measurements']
                measurement_timestep = timestep / len(measurements)
                for i, measurement in enumerate(measurements):
                    m_timestamp = timestamp + measurement_timestep * i
                    self._DATA[source_id][m_timestamp] = (m_timestamp, measurement_timestep, measurement)
        elif response.status == 401:
            # Unathenticated
            pass
        else:
            raise ConnectionError(response.status)


        if self.sensor_connection:
            self.sensor_connection.close()
        if self.other_connection:
            self.other_connection.close()
        


class CachedReader(Reader):
    def __init__(self, cache_token, reader):
        super().__init__()
        self.location_id = reader.location_id
        self.cache_token = cache_token
        if os.path.exists(f'cache/{self.cache_token}.json'):
            self.reader = JSONReader(self.location_id, [f'cache/{self.cache_token}.json'])
        else:
            self.reader = reader
        
    def load(self):
        self.reader.__enter__()
        self.reader.load()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not os.path.exists(f'cache/{self.cache_token}.json'):
            dicts = []
            for source_id in self.reader._DATA:
                for timestamp, (timestamp, timestep, value) in self.reader._DATA[source_id].items():
                    dicts.append(self.make_dict(source_id, timestamp, timestep, value))
            filename = f"cache/{self.cache_token}.json"
            with open(filename, 'w') as f:
                s = json.dumps(dicts).replace('\x13', '')
                f.write(s)

        self.reader.__exit__(exc_type, exc_val, exc_tb)

    def make_dict(self, source_id, timestamp, timestep, value):
        o = {
            'SourceId': source_id,
            'LocationId': self.location_id,
            'Data': {
                'Timestamp': timestamp*1000,
                'Timestep': timestep,
                'Measurements': [undateify(value)]
            }
        }
        return o

    def is_online(self):
        return True

    def __contains__(self, item):
        return super().__contains__(item) or item in self.reader

    def query(self, source_id, start_time, end_time):
        return self.reader.query(source_id, start_time, end_time)

    def __getitem__(self, item):
        source_id, target_time = item
        values = []
        if source_id in self._DATA:
            if isinstance(target_time, slice):
                start = target_time.start
                end = target_time.stop
                values += [val for time, val in self._DATA[source_id].items() if start < time <= end]
            else:
                values += [ self._DATA[source_id][target_time] ]
        elif source_id in self.reader._DATA:
            if isinstance(target_time, slice):
                start = target_time.start
                end = target_time.stop
                values += [val for time, val in self.reader._DATA[source_id].items() if start < time <= end]
            else:
                values += [ self.reader._DATA[source_id][target_time] ]
        return sorted(values)

   
def undateify(val):
    if type(val) == dict:
        for k in val:
            val[k] = undateify(val[k])
        return val
    elif type(val) == list:
        return [undateify(x) for x in val]
    elif type(val) == set:
        return {undateify(x) for x in val}
    elif type(val) not in [str, int, float, list, dict, set, bool, type(None)]:
        return str(val)
    else:
        return val

class MultiReader:
    def __init__(self, *readers):
        self._READERS = readers
        
    def __str__(self):
        return f"MultiReader({','.join(str(r) for r in self._READERS)})"
    
    def set_logger(self, logger):
        for r in self._READERS:
            r.set_logger(logger)
            
    def load(self):
        for r in self._READERS:
            r.load()
    
    def __enter__(self):
        self.load()
        for r in self._READERS:
            r.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for r in self._READERS:
            try:
                exit(r)
            except:
                continue

    def __contains__(self, item):
        for r in self._READERS:
            if item in r:
                return True
        return False

    def __getitem__(self, item):
        out = []
        for r in self._READERS:
            out.append(r[item])
        return out


    def is_online(self):
        for r in self._READERS:
            if r.is_online():
                return True
        return False
    
    def query(self, source_id, start_time, end_time):
        for r in self._READERS:
            r.query(source_id, start_time, end_time)

    def add_entries(self, source_id, entries):
        # inject the entries only into the first reader
        self._READERS[0].add_entries(source_id, entries)
        