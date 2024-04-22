from pm.data_handler import DataHandler

import datetime
import pm.features as features

import pytz

from .utils import human_time, f_timestamp, align_start_time, align_end_time

class FeatureCalculator(DataHandler):
    def __init__(self, location_id, data_input, data_output, features, start_time=None, end_time=None, profile={}, verbosity=0):
        super().__init__(location_id, data_input, data_output, profile={}, verbosity=verbosity)

        self.features = features

        self.start_time = None if start_time is None else start_time.timestamp()
        self.end_time = end_time.timestamp() if end_time is not None else datetime.datetime.utcnow().timestamp()

        self.data_output.set_descriptor(f"{self.location_id}_{f_timestamp(self.end_time)}")

    def run(self):
        self.print((f_timestamp(self.start_time), f_timestamp(self.end_time), self.end_time-self.start_time), 1)
        dependencies = {'raw': {}, 'calculated': {}, 'model': {}}
        missing = {'raw': [], 'calculated': [], 'model': []}

        self.data_output.set_descriptor(f"{self.location_id}")

        for feature in self.features:
            window = human_time(features.FEATURES[feature]['window'])
            end_time = align_end_time(self.end_time, window)
            self.print(f"Aligned endtime for {feature} is {f_timestamp(end_time)}", 4)
            if self.start_time is None:
                start_time = end_time - window
            else:
                start_time = align_start_time(self.start_time, window)
            if start_time < end_time:
                self.request_dependencies(feature, start_time, end_time, dependencies, missing)
        
        self.print("Requested dependencies.", 2)
        self.print(dependencies, 3)

        self.calculate_unmet(missing, force_store=self.features)
        self.print("Calculated features.", 1)
