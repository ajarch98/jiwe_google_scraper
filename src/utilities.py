import os
import json

class ScraperUtilities:
    @staticmethod
    def get_config():
        file_dir = os.path.dirname(os.path.realpath('__file__'))
        file_dir = os.path.abspath(f'{file_dir}/..')
        file_path = os.path.join(file_dir, 'config.json')
        with open(file_path, 'r') as f:
            # print(f.readlines())
            config = json.loads(f.read())
        assert config
        return config

    @staticmethod
    def get_if_exists(session, obj, _attr):
        _class = type(obj)
        _val = getattr(obj, _attr)

        existing_obj = session.query(_class).filter(
            getattr(_class, _attr)==_val
        ).one_or_none()

        return existing_obj


