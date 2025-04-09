import datetime, sys, os, traceback, pytz

from .utils import human_time, merge_intervals, f_timestamp

from .data_handler import DataHandler

class PipelineManager(DataHandler):
   
    force_calculate : list
   
    class FeatureNode:
        __NODES = {}

        def __init__(self, source_id):
            self.source_id = source_id
            self.dependencies = []
            self.dependees = []

        def __str__(self):
            return f'<FN: {self.source_id}>'

        def __repr__(self):
            return str(self)

        def add_dependency(self, node):
            if node not in self.dependencies:
                self.dependencies.append(node)
            if self not in node.dependees:
                node.dependees.append(self)

        @staticmethod
        def create_node(source_id):
            if source_id not in PipelineManager.FeatureNode.__NODES:
                node = PipelineManager.FeatureNode(source_id)
                PipelineManager.FeatureNode.__NODES[source_id] = node
            else:
                node = PipelineManager.FeatureNode.__NODES[source_id]
            return node

        @staticmethod
        def reset():
            PipelineManager.FeatureNode.__NODES = {}

        def walk(self):
            queue = [self]
            while queue:
                node = queue.pop(0) 
                queue += node.dependencies
                if node.source_id != '@':
                    yield node

    class DependencyNode:
        __NODES = {}

        def __init__(self, source_id, start_time, end_time):
            self.source_id = source_id
            self.start_time = start_time
            self.end_time = end_time
            self.dependencies = []
            self.dependees = []
            self.met = False

        def __str__(self):
            return f'<{self.source_id} - {self.start_time} : {self.end_time}>'

        def __repr__(self):
            return str(self)

        def add_dependency(self, node):
            if node not in self.dependencies:
                self.dependencies.append(node)
            if self not in node.dependees:
                node.dependees.append(self)
                
        def meet(self):
            self.met = True

        @staticmethod
        def create_node(source_id, start_time, end_time):
            if source_id not in PipelineManager.DependencyNode.__NODES:
                PipelineManager.DependencyNode.__NODES[source_id] = {}
            if (start_time, end_time) not in PipelineManager.DependencyNode.__NODES[source_id]:
                node = PipelineManager.DependencyNode(source_id, start_time, end_time)
                PipelineManager.DependencyNode.__NODES[source_id][(start_time, end_time)] = node
            else:
                node = PipelineManager.DependencyNode.__NODES[source_id][(start_time, end_time)]
            return node
        
        @staticmethod
        def reset():
            PipelineManager.DependencyNode.__NODES = {}
            
        @staticmethod
        def get_nodes(source_id):
            return PipelineManager.DependencyNode.__NODES.get(source_id, {})
        
        def walk(self):
            queue = [self]
            while queue:
                node = queue.pop(0) 
                queue += node.dependencies
                if node.source_id != '@':
                    yield node

    class ModelNotFoundError(Exception):
        def __init__(self, missing):
            self.missing = missing
        def __str__(self):
            return "Model not found: " + self.missing
        pass

    def __init__(self, location_id, data_input, data_output, pipeline, features, profile={}, forced_time=None, verbosity=0, force_calculate=[]):
        super().__init__(location_id, data_input, data_output, features, profile=profile, force_calculate=force_calculate, verbosity=verbosity)

        self.pipeline = pipeline
        self.pipeline_name = pipeline['name']
        
        self.forced_time = forced_time
        
        PipelineManager.force_calculate = force_calculate

    def get_time(self):
        if self.forced_time is None:
            return pytz.utc.localize(datetime.datetime.utcnow())
        else:
            return self.forced_time

    def pipeline_window(self):
        return human_time(self.pipeline['recurrence'] if isinstance(self.pipeline['recurrence'], str) else self.pipeline['recurrence']['period'])

    def pipeline_offset(self):
        return datetime.timedelta(seconds=human_time(self.pipeline['recurrence'].get('offset', '0h')) if isinstance(self.pipeline['recurrence'], dict) else 0)

    def calculate_runtime(self):
        # Calculate last timestamp according to the pipeline configuration
        location_tz = pytz.timezone(self.profile['timezone'])
        utc_now = self.get_time()
        users_time = utc_now.astimezone(location_tz)
        midnight_for_user = location_tz.localize(datetime.datetime.combine(users_time.date(), datetime.time.min))

        window = self.pipeline_window()
        offset = self.pipeline_offset()

        # Calculate the latest time for which the sensor data should be present
        # This is the timestamp for which the pipeline needs to trigger
        time = (midnight_for_user + offset).timestamp()
        time += ((users_time.timestamp() - time) // window) * window
        
        self.print(f"Calculated time {time} with period {window}", 2)

        return time

    def pipeline_dependencies(self, end_time):
        dependencies = {'raw': {}, 'calculated': {}}
        missing = {'raw': [], 'calculated': []}
        
        pipeline_window = self.pipeline_window()

        for output in self.pipeline['outputs']:
            self.request_dependencies(output, end_time - pipeline_window, end_time, dependencies, missing)

        if 'parameters' in self.pipeline:
            for parameter in self.pipeline['parameters']:
                self.request_dependencies(parameter, end_time - pipeline_window, end_time, dependencies, missing)

        return dependencies, missing


    # def run_models(self, runtime):
    #     window = self.pipeline_window()

    #     model_outputs = {}
    #     try:
    #         self.print(f"Importing DEX models", 3)
    #         MODELS = [(m, import_module('.models.' + m['name'], 'pm')) for m in self.pipeline['models']['situation'] + [self.pipeline['models']['coaching'], self.pipeline['models']['rendering']] if m]
    #     except ModuleNotFoundError as e: 
    #         raise PipelineManager.ModelNotFoundError(e.name)
    #     else:
    #         for model, m in MODELS:
    #             loaded = self.data_input[model['output'], runtime - window:runtime]
    #             if loaded and not model['output'] in self.force_calculate:
    #                 self.print(f"Model {model['name']} output found in database.", 2)
    #                 model_outputs[model['output']] = loaded[-1][2]
    #             else:
    #                 model = self._MODELS[model['output']]
    #                 self.print(f"Running model {model['name']}", 2)
    #                 values = {}
    #                 all_outputs = True
    #                 for source_info in model['inputs']:
    #                     if type(source_info) == tuple:
    #                         source_id = source_info[0]
    #                     else:
    #                         source_id = source_info
    #                     try:
    #                         values[source_id] = self.data_input[source_id, runtime][0][2]
    #                     except:
    #                         all_outputs = False
    #                 if all_outputs:
    #                     # Use the proDEX library to calculate the selected output criteria
    #                     self.print(f"DEX model inputs are {values}", 3)

    #                     dex = getattr(m, model['output'])
                        
    #                     if model_type(dex) == 'crisp':
    #                         output = proDEX.classify({getattr(m, source_id): value for source_id, value in values.items()}, dex)
    #                         # Store the calculated criteria into the database and cache
    #                     elif model_type(dex) == 'probabilistic':
    #                         inputs = {
    #                             getattr(m, source_id): probabilify(value,  getattr(m, source_id)) for source_id, value in values.items()
    #                         }
    #                         output_distribution = proDEX.classify(inputs, dex)

    #                         output = sample_from_distribution(output_distribution)

    #                     self.data_output.add_entries(model['output'], [(runtime, window, output)])
    #                     self.data_input.add_entries(model['output'], [(runtime, window, output)])
    #                     model_outputs[model['output']] = output

    #                     self.print(f"Model {model['name']} finished successfully with output '{output}'.", 3)
    #                 else:
    #                     self.print(f"Model {model['name']} failed due to incomplete data!", 3)
        
    #         return model_outputs

    def run(self):
        self.print(f"---- RUNNING PIPELINE {self.pipeline_name} FOR LOCATION {self.location_id} ----", 1)
        start_time = datetime.datetime.utcnow()
        self.print(f"Starting at {start_time}", 2)
        try:
            runtime = self.calculate_runtime()
            self.print(f"Calculated runtime {f_timestamp(runtime)}.", 1)
            self.data_output.set_descriptor(f"{self.location_id}_{f_timestamp(runtime)}")
            try:
                self.print("Requesting dependencies from the database...", 2)

                self.print(f"Starting data loading at {datetime.datetime.utcnow()}", 2)
                missing = self.smart_request_dependencies(runtime)
                self.print(f"Data loading done at {datetime.datetime.utcnow()}", 2)
                
                self.print("Dependencies received.", 2)
                self.print(f"Missing: {missing}", 5)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                error_message = f"{exc_type}: {str(e)}, {fname}, {exc_tb.tb_lineno}\n{traceback.format_exc()}"

                self.print(f"FAILED TO CONNECT TO DATABASE, EXECUTION DISRUPTED")
                self.print(e, 2)
                raise e

            self.print("Calculated missing requirements.", 2)
            try:
                self.calculate_unmet(missing)
                self.print("Calculated unmet inputs.", 2)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                error_message = f"{exc_type}: {str(e)}, {fname}, {exc_tb.tb_lineno}\n{traceback.format_exc()}"
                self.print(f"FEATURE CALCULATION ERROR, EXECUTION DISRUPTED")
                self.print(error_message, 2)
                raise e

            self.print(f"PIPELINE EXECUTION SUCCESSFUL")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            error_message = f"{exc_type}: {str(e)}, {fname}, {exc_tb.tb_lineno}\n{traceback.format_exc()}"

            self.print(f"UNKNOWN ERROR, EXECUTION DISRUPTED")
            self.print(e, 2)
            raise e
        pipeline_outputs = {}
        #for output in self.pipeline['outputs']:
        for output_node in missing.dependencies:
            output = output_node.source_id
            end_time = output_node.end_time

            pipeline_outputs[output] = pipeline_outputs.get(output, [])
            pipeline_outputs[output] += self.data_input[output, end_time]

        end_time = datetime.datetime.utcnow()

        self.print(f"Outputs:", 1)
        for output, values in pipeline_outputs.items():
            self.print(f"\033[1;33;49m{output}: \033[1;32;49m{values}", 1)
        self.print("\u001b[0m", 1)
        self.print(f"Execution done at {end_time} (execution time: {(end_time - start_time).total_seconds()})", 2)
        return pipeline_outputs

    def generate_feature_dependency(self):
        # Calculate feature dependency hierarchy

        # Reset the dependency between pipeline executions
        PipelineManager.FeatureNode.reset()

        root = PipelineManager.FeatureNode.create_node('@')
        
        def recurse_dependency(source_id):
            node = PipelineManager.FeatureNode.create_node(source_id)
            
            f_type = self.s_type(source_id)

            if f_type == 'raw':
                pass
            elif f_type == 'calculated':
                definition = self.features[source_id]
                for inpt in definition['inputs']:
                    if isinstance(inpt, tuple):
                        in_source_id = inpt[0]
                    else:
                        in_source_id = inpt
                    in_node = recurse_dependency(in_source_id)
                    node.add_dependency(in_node)
            elif f_type == 'model':
                pass
                # ------------------ DEPRECATED ------------------
                # model = self._MODELS[source_id]

                # for inpt in model['inputs']:
                #     if isinstance(inpt, tuple):
                #         in_source_id = inpt[0]
                #     else:
                #         in_source_id = inpt
                #     in_node = recurse_dependency(in_source_id)
                #     node.add_dependency(in_node)
            return node                    

        for output in self.pipeline['outputs']:
            node = recurse_dependency(output)
            root.add_dependency(node)

        if 'parameters' in self.pipeline:
            for parameter in self.pipeline['parameters']:
                node = recurse_dependency(parameter)
                root.add_dependency(node)

        # DEPTHS = {}

        # nodes = root.dependencies[:]
        # DEPTHS['@'] = 0
        # while nodes:
        #     node = nodes.pop(0)
        #     DEPTHS[node.source_id] = max(DEPTHS[d.source_id] for d in node.dependees if d.source_id in DEPTHS) + 1
        #     nodes += node.dependencies

        return root


    def generate_time_dependency(self, end):

        # Reset the dependency between pipeline executions
        PipelineManager.DependencyNode.reset()

        def recursive_dependency(source_id, start_time, end_time, dependee):
            f_type = self.s_type(source_id)

            if f_type == 'raw':
                # Raw dependencies are added as complete intervals
                node = PipelineManager.DependencyNode.create_node(source_id, start_time, end_time)
                dependee.add_dependency(node)
            elif f_type == 'calculated':
                # Calculated features are broken into intervals based on their own windows
                definition = self.features[source_id]
                f_window = human_time(definition['window'])

                if f_window == 0:
                    f_window = end_time - start_time

                time = start_time

                while time + f_window <= end_time: # Assume perfect divisibility of intervals
                    node = PipelineManager.DependencyNode.create_node(source_id, time, time + f_window)
                    dependee.add_dependency(node)
                    for inpt in definition['inputs']:
                        if isinstance(inpt, tuple):
                            in_source_id = inpt[0]
                            in_window = human_time(inpt[1])
                        else:
                            in_source_id = inpt
                            in_window = f_window
                        recursive_dependency(in_source_id, time + f_window - in_window, time + f_window, node)
                    time += f_window
        start = end - self.pipeline_window()

        root = PipelineManager.DependencyNode.create_node('@', start, end) # @ represents the entire pipeline

        for output in self.pipeline['outputs']:
            recursive_dependency(output, start, end, root)

        if 'parameters' in self.pipeline:
            for parameter in self.pipeline['parameters']:
                recursive_dependency(parameter, start, end, root)
        
        return root


    def smart_request_dependencies(self, runtime):
        feature_dependency = self.generate_feature_dependency()

        time_dependency = self.generate_time_dependency(runtime)

        for dependency in feature_dependency.walk():
            if dependency.source_id == '@':
                continue
            source_id = dependency.source_id
            f_type = self.s_type(source_id)

            # Calculate all unmet nodes for this source_id
            unmet_nodes = [n for n in PipelineManager.DependencyNode.get_nodes(source_id).values() \
                            if source_id in self.force_calculate or (not n.met) and any(not d.met for d in n.dependees)]
            unmet_intervals = [(n.start_time, n.end_time) for n in unmet_nodes]

            unmet_merged = merge_intervals(unmet_intervals)
            if not f_type == "calculated" or self.features[source_id].get('store', False):
                for start, end in unmet_merged:
                    self.print(f"Querying {source_id}: {datetime.datetime.fromtimestamp(start)} -- {datetime.datetime.fromtimestamp(end)}", 5)
                    self.query_db(source_id, start, end)
            
            # Check if data was found for any unmet nodes
            for unmet_node in unmet_nodes:
                if self.data_input[source_id, unmet_node.start_time:unmet_node.end_time] and source_id not in self.force_calculate:
                    unmet_node.meet()
                
                            
               
        return time_dependency
