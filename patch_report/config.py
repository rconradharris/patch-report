import ConfigParser
import os


class ConfigError(Exception):
    pass


class ConfigFileNotFound(ConfigError):
    pass


class ConfigRequired(ConfigError):
    pass


class ConfigSectionNotFound(ConfigError):
    pass


_OPTION_REQUIRED = object()


_REQUIRED_SECTIONS = [
    'gerrit',
    'patch_report',
    'redmine',
    'web',
]


_OPTIONS_SCHEMA = {
    "email": {
        "hostname": {"type": "str",
                     "default": _OPTION_REQUIRED},
        "password": {"type": "str",
                     "default": _OPTION_REQUIRED},
        "port": {"type": "int",
                 "default": 25},
        "recipients": {"type": "str",
                       "default": _OPTION_REQUIRED},
        "sender": {"type": "str",
                   "default": _OPTION_REQUIRED},
        "username": {"type": "str",
                     "default": _OPTION_REQUIRED},
    },
    "gerrit": {
        "url": {"type": "str",
                "default": _OPTION_REQUIRED},
    },
    "github:": {
        "api_url": {"type": "str",
                    "default": _OPTION_REQUIRED},
        "token": {"type": "str",
                  "default": _OPTION_REQUIRED},
        "match_string": {"type": "str",
                         "default": _OPTION_REQUIRED},
    },
    "patch_report": {
        "cache_directory": {"type": "str",
                            "default": '/tmp'},
        "ignore_missing_series_file": {"type": "bool",
                                       "default": False},
        "patch_activity_days": {"type": "int",
                                "default": 7},
        "repo_directory": {"type": "str",
                           "default": _OPTION_REQUIRED},
    },
    "redmine": {
        "url": {"type": "str",
                "default": _OPTION_REQUIRED},
        "key": {"type": "str",
                "default": _OPTION_REQUIRED},
        "ignore_errors": {"type": "bool",
                          "default": False},
        "verify_cert": {"type": "bool",
                        "default": True},
    },
    "web": {
        "debug": {"type": "bool",
                  "default": False},
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


def _parse_section(cfg, section, section_schema, values):
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


def _load():
    cfg = ConfigParser.SafeConfigParser()

    for path in _SEARCH_PATH:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            cfg.read(path)
            break
    else:
        raise ConfigFileNotFound('Config not found in search path: %s' %
                                 _SEARCH_PATH)

    sections = cfg.sections()

    # Ensure all sections are present
    for section in _OPTIONS_SCHEMA.iterkeys():
        if ':' in section:
            continue

        if section not in sections and section in _REQUIRED_SECTIONS:
            raise ConfigSectionNotFound(section)

    for section in sections:
        if ':' in section:
            prefix, discriminator = section.split(':', 1)

            if prefix == 'github':
                _GITHUB_USERNAMES.append(discriminator)

            section_schema = _OPTIONS_SCHEMA[prefix + ':']
        else:
            section_schema = _OPTIONS_SCHEMA[section]

        _parse_section(cfg, section, section_schema, _CONFIG_VALUES)


_CONFIG_VALUES = {}


def get_section(section):
    if not _CONFIG_VALUES:
        _load()

    return _CONFIG_VALUES.get(section)


def get(section, key):
    if not _CONFIG_VALUES:
        _load()

    return get_section(section)[key]


def get_from_multi_section(prefix, discriminator, key):
    section = '%s:%s' % (prefix, discriminator)
    return get(section, key)


_GITHUB_USERNAMES = []


def get_github_usernames():
    if not _GITHUB_USERNAMES:
        _load()

    return _GITHUB_USERNAMES
