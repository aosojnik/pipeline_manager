import datetime
import logging

import sys, traceback

from .utils import human_time, get_callable, merge_intervals, align_start_time, f_timestamp

class DataHandler:
    class FeatureCalculationError(Exception):
        def __init__(self, source_id, time, window, inputs, exc, desc=""):
            self.source_id = source_id
            self.time = time
            self.window = window
            self.inputs = inputs
            self.exc = exc
            self.desc = desc

        
        def __str__(self):
            return f"Error calculating feature {self.source_id} for time {self.time} and window {self.window} ({repr(self.exc)}){self.desc}"

    def __init__(self, location_id, data_input, data_output, features, profile={}, verbosity=0, force_calculate=[]):
        self.location_id = location_id

        self.data_input = data_input
        self.data_input.set_logger(self)

        self.data_output = data_output
        self.data_output.set_logger(self)
        
        self.features = features

        self.profile = profile

        self.verbosity = verbosity

        self.force_calculate = force_calculate

        self.warnings = []

        self.load_profile()

        self.current_calculation = None

    def load_profile(self):
        # Add time zone into profile if missing
        if 'timezone' not in self.profile:
            if self.location_id[:2] == "SI":
                self.profile['timezone'] = 'Europe/Ljubljana'
            else:
                self.profile['timezone'] = 'UTC'

    @staticmethod
    def warning(message):
        try:
            w = None
            raise Exception
        except:
            frame = sys.exc_info()[2].tb_frame
            f = frame
        finally:
            while f:
                if isinstance(f.f_locals.get('self', None), DataHandler):
                    w = f.f_locals['self']
                    break
                f = f.f_back
            
        if w:
            w.warnings.append(f"[{w.current_calculation if w.current_calculation else w.__class__}] {message}")

    def print(self, text, min_verbosity=1):
        if self.verbosity >= min_verbosity:
            print(text)
        # Verbosity could be set for each environment from the logging.Envname.ini
        # If verbosity is set to WARNING only log entries with warning or above will be logged
        # 
        # LogLevel Values
        # 
        # CRITICAL 50
        # ERROR 40
        # WARNING 30
        # INFO 20
        # DEBUG 10
        # NONE 0
        # 
        logging.debug(text) if min_verbosity == 5 else logging.info(text)

    def query_db(self, source_id, start_time, end_time):
        if self.data_input.is_online():
            return self.data_input.query(source_id, start_time, end_time)
        else:
            # The loader is not online, all data is already loaded
            pass

    def s_type(self, source_id):
        return 'calculated' if source_id in self.features else 'raw'

    def request_dependencies(self, source_id, start_time, end_time, dependencies, missings, force_fetch=False):
        def dependency(start, end):
            typ = self.s_type(source_id)
            if source_id not in dependencies[typ]:
                dependencies[typ][source_id] = set()
            dependencies[typ][source_id].add( (start, end) )

        def missing(start, end):
            typ = self.s_type(source_id)
            missings[typ].append( (source_id, start, end) )

        typ = self.s_type(source_id)
        if source_id in dependencies[typ] and (start_time, end_time) in dependencies[typ][source_id]:
            # Dependency has already been added
            pass
        else:
            self.print(f"Calculating dependencies for {source_id} ({typ}): {start_time} -- {end_time}", 5)
            window = end_time - start_time

            self.query_db(source_id, start_time, end_time)

            if typ == 'raw':
                # Raw data dependencies are complete chunks
                dependency(start_time, end_time)
            elif typ == 'calculated':

                # Calculated features are broken into intervals based on their own windows
                definition = self.features[source_id]
                f_window = human_time(definition['window'])

                # If a feature has a window of 0, it can calculate the entire window at once
                # This should generally be features that are calculated from raw data, i.e., 
                # features that fill missing values
                if f_window == 0:
                    f_window = window

                time = start_time

                while time + f_window <= end_time: # Assume perfect divisibility of intervals
                    dependency(time, time + f_window)

                    if (source_id, time + f_window) not in self.data_input or source_id in self.force_calculate or force_fetch:
                        # If the data is missing reucursively request dependencies
                        for inpt in definition['inputs']:
                            if isinstance(inpt, tuple):
                                in_source_id = inpt[0]
                                in_window = human_time(inpt[1])
                            else:
                                in_source_id = inpt
                                in_window = f_window

                            self.request_dependencies(in_source_id, time + f_window - in_window, time + f_window, dependencies, missings, source_id in self.force_calculate or force_fetch)

                        missing(time, time + f_window)

                    time += f_window
            else:
                # Missing model dependency
                model = self._MODELS[source_id]
                source_id = model['output']

                # TODO Make this work also for the Feature calculator
                pipeline_window = human_time(self.pipeline['recurrence'] if isinstance(self.pipeline['recurrence'], str) else self.pipeline['recurrence']['period'])
                pipeline_offset = human_time(self.pipeline['recurrence'].get('offset', '0h')) if isinstance(self.pipeline['recurrence'], dict) else 0

                # time = align_start_time(start_time, pipeline_window, pipeline_offset)
                # print(f_timestamp(time + pipeline_window), f_timestamp(end_time))
                # while time + pipeline_window <= end_time:
                dependency(start_time, end_time)

                for inpt in model['inputs']:
                    if isinstance(inpt, tuple):
                        source_id = inpt[0]
                        window = human_time(inpt[1])
                    else:
                        source_id = inpt
                        window = pipeline_window
                    # TODO Reslove input timing inconsistencies
                    self.request_dependencies(source_id, start_time, end_time, dependencies, missings)
                    
                    # time += pipeline_window

    def calculate_unmet(self, missing, force_store=set()):
        def resolve(source_id, start_time, end_time):
            feature = self.features[source_id]
            window = human_time(feature['window'])
            if window == 0:
                # if window = 0, calculate the entire interval in one go
                window = end_time - start_time
            assert (end_time - start_time) % window == 0
            time = start_time
            while time + window <= end_time:
                time += window
                self.print(f"Calculating {source_id} for time {time} (window {window})", 3)

                inputs = {}

                for inpt in feature['inputs']:
                    if isinstance(inpt, str):
                        in_source_id, in_window = inpt, window
                    else:
                        in_source_id, in_window = inpt[0], human_time(inpt[1])
                    in_source_type = self.s_type(in_source_id)
                    if in_source_type == 'calculated' and in_source_id in missing['calculated'] and \
                       (time - in_window, time) in missing['calculated'][in_source_id]:
                        resolve(in_source_id, time - in_window, time)
                    
                    if in_source_id not in inputs:
                        inputs[in_source_id] = []
                    inputs[in_source_id] += self.data_input[in_source_id, time - in_window:time]

                self.print(f"Calculating feature {source_id}.", 4)
                # Load the function that calculates the value
                f = get_callable(feature['function'])
                # Calculate the missing data point
                self.current_calculation = f"{source_id} @ {time} ({window})"
                try:
                    data_points = f(time, window, inputs)
                except Exception as e:
                    if 'default' in feature:
                        data_points = [(time, window, feature['default'])]
                        DataHandler.warning(f"Used default value!")
                    else:
                        raise DataHandler.FeatureCalculationError(source_id, time, window, inputs, e, desc=f"\n{traceback.format_exc()}")
                finally:
                    self.current_calculation = None

                self.print(f"Feature {source_id} calculated for {time}.", 4)

                # Make a JSON for storing into the database
                #j_point = self.make_json(source_id, end_time, timestep, data_point)
                #self.print(j_point, 5)
                if feature.get('store', False) or source_id in force_store:
                    # Some values may not need to be stored into the database
                    self.print(f"Storing feature {source_id} into the database.", 4)  
                    self.data_output.add_entries(source_id, data_points)

                # All values are stored into the cache, so repeated lookups into
                # the database are not necessary
                self.print(f"Storing feature {source_id} into the cache.", 4)  
                self.data_input.add_entries(source_id, data_points)
                if (time - window, time) in missing[source_id]:
                    missing[source_id].remove((time - window, time))
        
        for source_id in missing:
            while missing[source_id]:
                start_time, end_time = missing[source_id].pop()
                resolve(source_id, start_time, end_time)
