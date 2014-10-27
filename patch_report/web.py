import datetime
import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

import patch_report
from patch_report import cache
from patch_report import config
from patch_report.models.project import get_project_from_cache


def _render_empty_cache_page():
    return render_template('empty_cache.html')


def _is_data_stale(projects, stale_secs=600):
    last_updated_at = patch_report.get_last_updated_at(projects[0])
    utcnow = datetime.datetime.utcnow()
    updated_secs = (utcnow - last_updated_at).total_seconds()
    return updated_secs > stale_secs


def _common(sidebar_tab, projects=None):
    if projects is None:
        projects = config.get_projects()

    stale_data = _is_data_stale(projects)

    return dict(
            projects=projects,
            sidebar_tab=sidebar_tab,
            stale_data=stale_data,
            )


@app.route('/')
def overview():
    projects = config.get_projects()

    overview_counts_by_project = {}
    for project in projects:
        try:
            project_obj = get_project_from_cache(project)
        except cache.CacheFileNotFound:
            return _render_empty_cache_page()

        overview_counts = project_obj.patch_series.get_overview_counts()
        overview_counts_by_project[project] = overview_counts

    return render_template('overview.html',
                           overview_counts_by_project=overview_counts_by_project,
                           **_common('Overview', projects=projects)
                           )


@app.route('/upstream-reviews')
def upstream_reviews():
    projects = config.get_projects()

    upstream_reviews_by_project = {}
    for project in projects:
        try:
            project_obj = get_project_from_cache(project)
        except cache.CacheFileNotFound:
            return _render_empty_cache_page()

        upstream_reviews = project_obj.patch_series.get_upstream_reviews()
        upstream_reviews_by_project[project] = upstream_reviews


    return render_template('upstream_reviews.html',
                           upstream_reviews_by_project=upstream_reviews_by_project,
                           **_common('Upstream Reviews', projects=projects)
                           )


@app.route('/<project_name>')
def project_view(project_name):
    return redirect(url_for('project_patches', project_name=project_name))


def _project_common(project, project_tab):
    return dict(
            last_updated_at=project.get_last_updated_at(),
            project=project,
            project_tab=project_tab,
            **_common(project.name)
            )


@app.route('/<project_name>/patches')
def project_patches(project_name):
    try:
        project = get_project_from_cache(project_name)
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    sort_key = request.args.get('sort_key', 'idx')
    sort_dir = request.args.get('sort_dir', 'desc')
    patches = project.patch_series.get_sorted_patches(sort_key, sort_dir)

    return render_template('project/patches.html',
                           patches=patches,
                           sort_dir=sort_dir,
                           sort_key=sort_key,
                           **_project_common(project, 'Patches')
                           )


@app.route('/<project_name>/stats')
def project_stats(project_name):
    try:
        project = get_project_from_cache(project_name)
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    patch_series = project.patch_series
    author_counts = patch_series.get_author_counts()
    category_counts = patch_series.get_category_counts()

    return render_template('project/stats.html',
                           author_counts=author_counts,
                           category_counts=category_counts,
                           **_project_common(project, 'Stats')
                           )


def _init_app(app):
    app.debug = config.get('web', 'debug')


_init_app(app)


if __name__ == '__main__':
    app.run()
