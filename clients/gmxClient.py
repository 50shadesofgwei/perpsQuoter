from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager
import os
from dotenv import load_dotenv
load_dotenv()
PATH_TO_GMX_CONFIG_FILE = os.getenv('PATH_TO_GMX_CONFIG_FILE')


def get_config_object() -> ConfigManager:
    config_object = ConfigManager(chain='arbitrum')
    config_object.set_config(PATH_TO_GMX_CONFIG_FILE)

    return config_object

ARBITRUM_CONFIG_OBJECT = get_config_object()

