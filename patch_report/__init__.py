from patch_report import cache
from patch_report import config
from patch_report.models import patch_series
from patch_report.models import project


def refresh_projects(clear=False):
    if clear:
        cache.clear()

    project_names = config.get_project_names()
    for project_name in project_names:
        proj = project.get_project(project_name)
        proj.refresh()


def get_last_updated_at(project_name):
    return cache.get_last_updated_at(project_name)
