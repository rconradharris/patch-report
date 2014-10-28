import datetime
import os
import urlparse

from patch_report import config
from patch_report import cache
from patch_report import utils
from patch_report.models import patch_series


def _get_project_config(project_name, key):
    return config.get('project:%s' % project_name, key)


def get_project_from_cache(project_name):
    return cache.read_file(project_name)


def get_projects_from_cache():
    return [get_project_from_cache(n) for n in config.get_project_names()]


def refresh_projects(clear=False):
    if clear:
        cache.clear()

    for project_name in config.get_project_names():
        repo_directory = config.get('patch_report', 'repo_directory')
        github_url = _get_project_config(project_name, 'github_url')

        project = Project(project_name, repo_directory, github_url)

        project.patch_series = patch_series.PatchSeries(project)
        project.refresh()
        cache.write_file(project.name, project)


class Project(object):
    def __init__(self, name, repo_directory, github_url):
        self.name = name
        self.repo_directory = repo_directory
        self.github_url = github_url

    @property
    def repo_path(self):
        repo_name = os.path.basename(self.github_url)
        return os.path.join(self.repo_directory, repo_name)

    def _get_github_ssh_url(self):
        parsed = urlparse.urlparse(self.github_url)
        path_parts = parsed.path.split('/')
        # Ignore first slash at [0]
        org = path_parts[1]
        repo = path_parts[2]
        return "git@%(netloc)s:%(org)s/%(repo)s.git" % dict(
                netloc=parsed.netloc, org=org, repo=repo)

    def refresh(self):
        if os.path.exists(self.repo_path):
            with utils.temp_chdir(self.repo_path):
                os.system('git checkout master && git fetch origin'
                          ' && git merge origin/master')
        else:
            ssh_url = self._get_github_ssh_url()
            with utils.temp_chdir(os.path.dirname(self.repo_path)):
                os.system('git clone %s' % ssh_url)

        self.patch_series.refresh()

    @property
    def last_updated_at(self):
        return cache.get_last_updated_at(self.name)

    def is_data_stale(self, stale_secs=600):
        utcnow = datetime.datetime.utcnow()
        updated_secs = (utcnow - self.last_updated_at).total_seconds()
        return updated_secs > stale_secs
