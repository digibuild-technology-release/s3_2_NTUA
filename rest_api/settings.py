from configparser import ConfigParser


def read_config_file():
    config_object = ConfigParser()
    config_object.read("config.ini")
    return config_object


config_object = read_config_file()

DIGIBUILD_PG = {
    'HOSTNAME': config_object.get('DIGIBUILDPG', 'DIGIBUILD_POSTGRES_HOST'),
    'PORT': config_object.get('DIGIBUILDPG', 'DIGIBUILD_POSTGRES_EXT_PORT'),
    'USER': config_object.get('DIGIBUILDPG', 'DIGIBUILD_POSTGRES_USER'),
    'PASSWORD': config_object.get('DIGIBUILDPG', 'DIGIBUILD_POSTGRES_PASSWORD'),
    'DB': config_object.get('DIGIBUILDPG', 'DIGIBUILD_POSTGRES_DB')
}

BUILDING_LIST = [286, 263, 272, 284, 279]