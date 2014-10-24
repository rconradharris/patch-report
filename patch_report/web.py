import datetime
import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

import patch_report
from patch_report import cache
from patch_report import config

STALE_DATA_SECS = 600


def _render_empty_cache_page():
    return render_template('empty_cache.html')


@app.route('/')
def overview():
    projects = config.get_projects()

    overview_counts_by_project = {}
    for project in projects:
        try:
            patch_series = patch_report.get_patch_series(project)
        except cache.CacheFileNotFound:
            return _render_empty_cache_page()

        overview_counts = patch_series.get_overview_counts()
        overview_counts_by_project[project] = overview_counts

    return render_template('overview.html',
                           overview_counts_by_project=overview_counts_by_project,
                           projects=projects,
                           sidebar_tab='Overview',
                           )


@app.route('/upstream-reviews')
def upstream_reviews():
    projects = config.get_projects()

    upstream_reviews_by_project = {}
    for project in projects:
        try:
            patch_series = patch_report.get_patch_series(project)
        except cache.CacheFileNotFound:
            return _render_empty_cache_page()

        upstream_reviews = patch_series.get_upstream_reviews()
        upstream_reviews_by_project[project] = upstream_reviews

    return render_template('upstream_reviews.html',
                           projects=projects,
                           sidebar_tab='Upstream Reviews',
                           upstream_reviews_by_project=upstream_reviews_by_project,
                           )


@app.route('/<project>')
def project(project):
    return redirect(url_for('project_patches', project=project))


def _project_common(project):
    last_updated_at = patch_report.get_last_updated_at(project)
    projects = config.get_projects()

    utcnow = datetime.datetime.utcnow()
    updated_secs = (utcnow - last_updated_at).total_seconds()
    stale_data = updated_secs > STALE_DATA_SECS

    return dict(
            last_updated_at=last_updated_at,
            project=project,
            projects=projects,
            sidebar_tab=project,
            stale_data=stale_data,
            )


@app.route('/<project>/patches')
def project_patches(project):
    try:
        patch_series = patch_report.get_patch_series(project)
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    common = _project_common(project)

    sort_key = request.args.get('sort_key', 'idx')
    sort_dir = request.args.get('sort_dir', 'desc')

    patches = patch_series.get_sorted_patches(sort_key, sort_dir)

    github_url = config.get_for_project(project, 'github_url')

    return render_template('project/patches.html',
                           github_url=github_url,
                           patches=patches,
                           patch_series=patch_series,
                           project_tab='Patches',
                           sort_dir=sort_dir,
                           sort_key=sort_key,
                           **common
                           )


@app.route('/<project>/stats')
def project_stats(project):
    try:
        patch_series = patch_report.get_patch_series(project)
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    common = _project_common(project)

    author_counts = patch_series.get_author_counts()
    category_counts = patch_series.get_category_counts()

    return render_template('project/stats.html',
                           author_counts=author_counts,
                           category_counts=category_counts,
                           patch_series=patch_series,
                           project_tab='Stats',
                           **common
                           )


def _init_app(app):
    app.debug = config.get('web', 'debug')


_init_app(app)


if __name__ == '__main__':
    app.run()
