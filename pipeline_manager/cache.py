class Cache():
    def __init__(self):
        self._DATA = {}
    def __str__(self):
        return self.__class__.__name__

    def set_logger(self, logger):
        self._LOGGER = logger

    def log(self, msg, level):
        self._LOGGER.print(f"[{self}] {msg}", level)

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

    def __contains__(self, item):
        source_id, timestamp = item
        return source_id in self._DATA and timestamp in self._DATA[source_id]

    def add_entries(self, source_id, entries):
        if source_id not in self._DATA:
            self._DATA[source_id] = {}
        for entry in entries:
            timestamp = entry[0]
            self._DATA[source_id][timestamp] = entry
