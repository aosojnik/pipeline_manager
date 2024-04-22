import csv
import datetime
import json

class Writer:
    def __init__(self, location_id):
        self.location_id = location_id
        self.runtime = None
        self._DATA = {}
        self.descriptor = ''

    def __str__(self):
        return self.__class__.__name__

    def set_logger(self, logger):
        self._LOGGER = logger

    def log(self, msg, level):
        self._LOGGER.print(f"[{self}] {msg}", level)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def add_entries(self, source_id, entries):
        if source_id not in self._DATA:
            self._DATA[source_id] = {}
        for entry in entries:
            timestamp = entry[0]
            self._DATA[source_id][timestamp] = entry

    def set_descriptor(self, descriptor):
        self.descriptor = descriptor

class CSVWriter(Writer):
    def __init__(self, location_id, target):
        super().__init__(location_id)
        self.target = target

    def __exit__(self, exc_type, exc_val, exc_tb):
        timespans = {}
        headers = {}
        for source_id in sorted(self._DATA.keys()):
            for timestamp, (timestamp, timespan, value) in sorted(self._DATA[source_id].items()):
                if timespan not in timespans:
                    timespans[timespan] = {}
                    headers[timespan] = []
                if timestamp not in timespans[timespan]:
                    timespans[timespan][timestamp] = {}
                if source_id not in headers[timespan]:
                    headers[timespan].append(source_id)
                timespans[timespan][timestamp][source_id] = value

        now = datetime.datetime.now()

        for timespan in timespans:
            filename = f"{self.descriptor}_{timespan}s.csv"
            with open(f"{self.target}/{filename}", 'w') as f:
                header = ['timestamp'] + headers[timespan]
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()

                for timestamp, values in timespans[timespan].items():
                    values['timestamp'] = timestamp
                    writer.writerow(values)


class JSONWriter(Writer):
    def __init__(self, location_id, target):
        super().__init__(location_id)
        self.target = target

    def make_dict(self, source_id, timestamp, timestep, value):
        o = {
            'sourceId': source_id,
            'locationId': self.location_id,
            'timestamp': timestamp,
            'timestep': timestep,
            'values': [value]
        }
        return o

    def __exit__(self, exc_type, exc_val, exc_tb):
        dicts = []
        for source_id in self._DATA:
            for timestamp, (timestamp, timespan, value) in self._DATA[source_id].items():
                dicts.append(self.make_dict(source_id, timestamp, timespan, value))
        filename = f"{self.descriptor}.json".replace(':', '_')
        with open(f"{self.target}/{filename}", 'w') as f:
            json.dump(dicts, f)
