#!/usr/bin/env python
"""
Patch-Repo Web Overview Tool

From command-line run:
    python patch_report/web.py

From webrowser navigate to:
    http://localhost:5000
"""
import datetime
import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

import patch_report
from patch_report import config

STALE_DATA_SECS = 600


@app.route('/')
def overview():
    projects = config.get_projects()

    overview_counts_by_project = {}
    for project in projects:
        patch_series = patch_report.get_patch_series(project)
        overview_counts = patch_series.get_overview_counts()
        overview_counts_by_project[project] = overview_counts

    return render_template('overview.html',
                           overview_counts_by_project=overview_counts_by_project,
                           projects=projects,
                           sidebar_tab='Overview',
                           )


@app.route('/<project>')
def project(project):
    return redirect(url_for('project_patches', project=project))


def _project_common(project):
    patch_series = patch_report.get_patch_series(project)
    last_updated_at = patch_report.get_last_updated_at(project)
    projects = config.get_projects()

    utcnow = datetime.datetime.utcnow()
    updated_secs = (utcnow - last_updated_at).total_seconds()
    stale_data = updated_secs > STALE_DATA_SECS

    return dict(
            last_updated_at=last_updated_at,
            patch_series=patch_series,
            project=project,
            projects=projects,
            sidebar_tab=project,
            stale_data=stale_data,
            )


@app.route('/<project>/patches')
def project_patches(project):
    common = _project_common(project)

    sort_key = request.args.get('sort_key', 'idx')
    sort_dir = request.args.get('sort_dir', 'desc')

    patch_series = common['patch_series']
    patches = patch_series.get_sorted_patches(sort_key, sort_dir)

    github_url = config.get_for_project(project, 'github_url')

    return render_template('project/patches.html',
                           github_url=github_url,
                           patches=patches,
                           project_tab='Patches',
                           sort_dir=sort_dir,
                           sort_key=sort_key,
                           **common
                           )


@app.route('/<project>/stats')
def project_stats(project):
    common = _project_common(project)

    patch_series = common['patch_series']
    author_counts = patch_series.get_author_counts()
    category_counts = patch_series.get_category_counts()

    return render_template('project/stats.html',
                           author_counts=author_counts,
                           category_counts=category_counts,
                           project_tab='Stats',
                           **common
                           )


def _init_app(app):
    app.debug = config.get('web', 'debug')


_init_app(app)


if __name__ == '__main__':
    app.run()
