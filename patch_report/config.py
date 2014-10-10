import ConfigParser
import os


class ConfigError(Exception):
    pass


class ConfigFileNotFound(ConfigError):
    pass


class ConfigRequired(ConfigError):
    pass


_OPTION_REQUIRED = object()


_OPTIONS_SCHEMA = {
    "patch_report": {
        "repo_path": {"type": "str",
                      "default": _OPTION_REQUIRED},
        "data_directory": {"type": "str",
                           "default": '/tmp'},
    },
    "redmine": {
        "url": {"type": "str",
                "default": _OPTION_REQUIRED},
        "username": {"type": "str",
                     "default": _OPTION_REQUIRED},
        "password": {"type": "str",
                     "default": None},
    },
    "web": {
        "debug": {"type": "bool",
                  "default": False},
        "host": {"type": "str",
                 "default": None},
        "port": {"type": "int",
                 "default": None},
    },
}


_SEARCH_PATH = ['./patch_report.cfg',
               '~/.patch_report.cfg',
               '/etc/patch_report.cfg']


def _get_value(cfg, section, key, type_):
    if type_ == 'bool':
        getter = cfg.getboolean
    elif type_ == 'float':
        getter = cfg.getfloat
    elif type_ == 'int':
        getter = cfg.getint
    else:
        getter = cfg.get

    return getter(section, key)


_CONFIG_VALUES = None


def _load():
    global _CONFIG_VALUES

    cfg = ConfigParser.SafeConfigParser()

    for path in _SEARCH_PATH:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            cfg.read(path)
            break
    else:
        raise ConfigFileNotFound('Config not found in search path: %s' %
                                 _SEARCH_PATH)

    values = {}
    for section, section_schema in _OPTIONS_SCHEMA.iteritems():
        for key, option_schema in section_schema.iteritems():
            try:
                value = _get_value(
                        cfg, section, key, option_schema['type'])
            except ConfigParser.NoOptionError:
                default_value = option_schema['default']
                if default_value is _OPTION_REQUIRED:
                    raise ConfigRequired(
                            "%s.%s is required" % (section, key))
                value = default_value

            if section not in values:
                values[section] = {}

            values[section][key] = value

    _CONFIG_VALUES = values


def get(section, key):
    if _CONFIG_VALUES is None:
        _load()

    return _CONFIG_VALUES[section][key]
