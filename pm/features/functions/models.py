import joblib

import os

MODELS = {}


def load_model(name):
    if name not in MODELS:
        model = joblib.load(os.path.join(os.path.split(__file__)[0], 'ml_models', f'{name}.joblib'))
        MODELS[name] = model
    return MODELS[name]

def run_ml_model(model_name):
    def ml_model(timestamp, timestep, inputs):
        model = load_model(model_name)
        predictions = []
        for vvec in zip(*inputs.values()):
            timestamp = vvec[0][0]
            timestep = vvec[0][1]
            vector = [x[2] for x in vvec]
            try:
                prediction = model.predict([vector])[0]
            except ValueError:
                prediction = "not_calculated"
            finally:
                predictions.append((timestamp, timestep, prediction))
        return predictions
    return ml_model

