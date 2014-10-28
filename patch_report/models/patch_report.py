from __future__ import absolute_import
from patch_report import config
from patch_report import cache
from patch_report.models.project import Project
from patch_report.models.patch_series import PatchSeries


def get_from_cache():
    return cache.read_file('patch_report')


def refresh(clear_cache=False):
    if clear_cache:
        cache.clear()

    repo_directory = config.get('patch_report', 'repo_directory')
    patch_report = PatchReport(repo_directory)
    patch_report.refresh()

    cache.write_file('patch_report', patch_report)


class PatchReport(object):
    def __init__(self, repo_directory):
        self.repo_directory = repo_directory
        self._projects = {}

    @property
    def projects(self):
        return self._projects.values()

    def get_project(self, project_name):
        return self._projects[project_name]

    def refresh(self):
        for project_name in config.get_project_names():
            github_url = config.get('project:%s' % project_name, 'github_url')

            project = Project(self, project_name, github_url)
            project.patch_series = PatchSeries(project)
            project.refresh()

            self._projects[project_name] = project
