import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

import patch_report
from patch_report import cache
from patch_report import config
from patch_report.models.project import (
    get_project_from_cache,
    get_projects_from_cache,
)


def _render_empty_cache_page():
    return render_template('empty_cache.html')


def _common(sidebar_tab, projects):
    return dict(
            projects=projects,
            sidebar_tab=sidebar_tab,
            stale_data=projects[0].is_data_stale(),
            )


@app.route('/')
def overview():
    try:
        projects = get_projects_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    overview_counts_by_project = {}
    for project in projects:
        overview_counts = project.patch_series.get_overview_counts()
        overview_counts_by_project[project] = overview_counts

    sort_key = request.args.get('sort_key', 'num_patches')
    sort_dir = request.args.get('sort_dir', 'desc')
    sorted_projects = sorted(projects,
        key=lambda p: overview_counts_by_project[p][sort_key],
        reverse=sort_dir == 'desc')

    return render_template('overview.html',
                           overview_counts_by_project=overview_counts_by_project,
                           sort_key=sort_key,
                           sort_dir=sort_dir,
                           sorted_projects=sorted_projects,
                           **_common('Overview', projects)
                           )


@app.route('/upstream-reviews')
def upstream_reviews():
    try:
        projects = get_projects_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    upstream_reviews_by_project = {}
    for project in projects:
        upstream_reviews = project.patch_series.get_upstream_reviews()
        upstream_reviews_by_project[project] = upstream_reviews


    return render_template('upstream_reviews.html',
                           upstream_reviews_by_project=upstream_reviews_by_project,
                           **_common('Upstream Reviews', projects)
                           )


@app.route('/<project_name>')
def project_view(project_name):
    return redirect(url_for('project_patches', project_name=project_name))


def _project_common(project, project_tab):
    projects = get_projects_from_cache()
    return dict(
            project=project,
            project_tab=project_tab,
            **_common(project.name, projects)
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
