import importlib.resources

import textx

from . import config


# utils
def parse(s):
    with importlib.resources.path(config, 'dsl.tx') as path:
        dsl = textx.metamodel_from_file(path)
    program = dsl.model_from_str(s)
    return program




