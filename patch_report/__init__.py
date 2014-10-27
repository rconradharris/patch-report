from patch_report import cache
from patch_report import config
from patch_report.models import patch_series
from patch_report.models import project


def refresh_projects(clear=False):
    if clear:
        cache.clear()

    projects = config.get_projects()
    for project_name in projects:
        proj = project.get_project(project_name)
        proj.refresh()


def get_last_updated_at(project_name):
    return cache.get_last_updated_at(project_name)
