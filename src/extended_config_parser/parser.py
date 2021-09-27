import configparser
import os
from typing import Dict


from dotenv import load_dotenv

load_dotenv()


class ExtendedConfigParser:
    def __init__(self, env_prefix: str = 'CONF') -> None:
        self.config = configparser.ConfigParser()
        self.env_prefix = env_prefix
        self._add_config_from_env()

    def _add_config_from_env(self) -> None:

        envs = os.environ
        config_dict: Dict[str, Dict[str, str]] = {}

        env_keys = list(envs)
        spitted_env_keys = [env_key.split('_') for env_key in env_keys]
        config_item_keys = list(filter(lambda x: x[0] == self.env_prefix, spitted_env_keys))

        for item in config_item_keys:
            section_key = item[1].lower()
            item_key = '_'.join([item.lower() for item in item[2:]])
            item_value = os.environ['_'.join(item)]

            if not config_dict.get(section_key):
                config_dict[section_key] = {}
            config_dict[section_key][item_key] = item_value

        self.config.read_dict(config_dict)

    def __getitem__(self, item: str) -> configparser.SectionProxy:
        try:
            return self.config.__getitem__(item)
        except KeyError:
            raise KeyError(f'Configuration item {item} is not set')

    def read(self, filepath: str) -> None:
        self.config.read(filepath)


if __name__ == "__main__":
    os.environ['XXX_SECTION_VAL_NAME'] = 'asdf'
    os.environ['XXX_SECTION_VAL_NAME2'] = '1234'
    os.environ['XXX_SECTION_VAL_NAME_aaa'] = 'ghjkl'
    os.environ['XXX_SECTION123_VAL_NAME'] = 'asdf'
    os.environ['XXX_SECTION555_VAL_NAME'] = 'asdf'

    config = ExtendedConfigParser(
        env_prefix="XXX"
    )

    config.read('./config.ini')

    set1 = config["section"]["val_name"]
    set2 = config["file"]["item"]

    print(set1)
    print(set2)
