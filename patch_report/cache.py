from patch_report import state


def _make_state_directory():
    return state.StateDirectory(subdirectory='cache')


def read_file(name):
    statedir = _make_state_directory()
    return statedir.read_file(name)


def write_file(name, data):
    statedir = _make_state_directory()
    return statedir.write_file(name, data)


def get_last_updated_at(name):
    statedir = _make_state_directory()
    return statedir.get_last_updated_at(name)


def clear():
    statedir = _make_state_directory()
    return statedir.clear()


class DictCache(object):
    def __init__(self, filename):
        self.filename = filename
        self.data = None

    def _load(self):
        try:
            self.data = read_file(self.filename)
        except state.FileNotFound:
            self.data = {}

    def __getitem__(self, key):
        if self.data is None:
            self._load()

        return self.data[key]

    def __setitem__(self, key, value):
        if self.data is None:
            self._load()

        self.data[key] = value
        write_file(self.filename, self.data)
