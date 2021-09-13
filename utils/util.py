import os

import yaml


def load_env_variables():
    with open("conf/env.yaml") as f:
        config = yaml.safe_load(f)
        for key, value in config.items():
            os.environ[key] = str(value)


def load_app_variables(input_key):
    with open("conf/app.yaml") as f:
        config = yaml.safe_load(f)
        for key, value in config.items():
            if input_key == key:
                return value
        return None
