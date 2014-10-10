import os

from patch_report import config
from patch_report.models import patch


class PatchSeries(object):
    def __init__(self):
        self.patches = []

    def refresh(self):
        repo_path = config.get('patch_report', 'repo_path')
        series_path = os.path.join(repo_path, 'series')

        idx = 1
        with open(series_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                p = patch.Patch(idx, line)
                p.refresh()
                self.patches.append(p)
                idx += 1

    def get_sorted_patches(self, sort_key, sort_dir):
        key = lambda p: getattr(p, sort_key)
        reverse = sort_dir == 'desc'
        return sorted(self.patches, key=key, reverse=reverse)
