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
    "gerrit": {
        "url": {"type": "str",
                "default": _OPTION_REQUIRED},
    },
    "patch_report": {
        "cache_directory": {"type": "str",
                            "default": '/tmp'},
    },
    "project:": {
        "github_url": {"type": "str",
                      "default": _OPTION_REQUIRED},
        "repo_path": {"type": "str",
                      "default": _OPTION_REQUIRED},
    },
    "redmine": {
        "url": {"type": "str",
                "default": _OPTION_REQUIRED},
        "username": {"type": "str",
                     "default": _OPTION_REQUIRED},
        "password": {"type": "str",
                     "default": None},
        "ignore_errors": {"type": "bool",
                          "default": False},
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


_CONFIG_VALUES = {}
_PROJECTS = []


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

    for section in cfg.sections():
        if ':' in section:
            prefix, rest = section.split(':', 1)

            if prefix == 'project':
                _PROJECTS.append(rest)

            section_schema = _OPTIONS_SCHEMA[prefix + ':']
        else:
            section_schema = _OPTIONS_SCHEMA[section]

        _parse_section(cfg, section, section_schema, _CONFIG_VALUES)


def get(section, key):
    if not _CONFIG_VALUES:
        _load()

    return _CONFIG_VALUES[section][key]


def get_for_project(project, key):
    return get('project:%s' % project, key)


def get_projects():
    if not _PROJECTS:
        _load()

    return _PROJECTS
