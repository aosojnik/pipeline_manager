from os.path import dirname, basename, isfile, join, split
import glob, importlib
modules = [
    f for f in glob.glob(join(dirname(__file__), "*.py"))
    if isfile(f) and not f.endswith('__init__.py') 
]

FEATURES = {}

for module in modules:
    name = split(module)[-1][:-3]
    FEATURES.update(getattr(importlib.import_module(f'.{name}', __package__), 'FEATURES', {}))