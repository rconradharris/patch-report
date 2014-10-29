from __future__ import absolute_import
import json

import requests

from patch_report import cache
from patch_report import config
from patch_report.simplelog import log


_GERRIT = None

def _load():
    global _GERRIT
    url = config.get('gerrit', 'url')
    _GERRIT = _Gerrit(url)


def get_from_line(patch, line):
    if 'Upstream-Change-Id' not in line:
        return

    change_id = line.split(' ', 1)[1].strip()

    if _GERRIT is None:
        _load()

    return _GERRIT.get_change(patch, change_id)


class GerritChange(object):
    def __init__(self, patch, change_id, subject=None, status=None):
        self.patch = patch
        self.change_id = change_id
        self.subject = subject
        self.status = status

    @property
    def is_merged(self):
        return self.status == 'MERGED'

    @property
    def label(self):
        return self.change_id[:5]

    @property
    def url(self):
        url = config.get('gerrit', 'url')
        return "%s/#q,%s,n,z" % (url, self.change_id)


class _Gerrit(object):
    def __init__(self, url):
        self.url = url
        self.cache = cache.DictCache('gerrit_reviews')

    def _fetch_remote_change(self, patch, change_id):
        log('Fetching Gerrit Change %s' % change_id)

        url = '%s/changes/?q=change:%s&n=1' % (self.url, change_id)
        resp = requests.get(url)

        # Strip magic prefix
        content = resp.content[4:]

        change_infos = json.loads(content)
        change_info = change_infos[0]

        return GerritChange(patch,
                            change_id,
                            subject=change_info['subject'],
                            status=change_info['status'])

    def get_change(self, patch, change_id):
        try:
            change = self.cache[change_id]
        except KeyError:
            pass
        else:
            return change

        change = self._fetch_remote_change(patch, change_id)
        self.cache[change_id] = change
        return change
