#!/usr/bin/env python
"""
Patch-Repo Web Overview Tool

From command-line run:
    python patch_report/web.py

From webrowser navigate to:
    http://localhost:5000
"""
import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

import patch_report
from patch_report import config


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


def _sidebar_for_project(project):
    projects = config.get_projects()
    return dict(sidebar_tab=project, projects=projects)


@app.route('/<project>/patches')
def project_patches(project):
    patch_series = patch_report.get_patch_series(project)
    last_updated_at = patch_report.get_last_updated_at(project)

    sort_key = request.args.get('sort_key', 'idx')
    sort_dir = request.args.get('sort_dir', 'desc')
    patches = patch_series.get_sorted_patches(sort_key, sort_dir)

    sidebar = _sidebar_for_project(project)
    github_url = config.get_for_project(project, 'github_url')

    return render_template('project/patches.html',
                           patches=patches,
                           project=project,
                           project_tab='Patches',
                           sort_key=sort_key,
                           sort_dir=sort_dir,
                           last_updated_at=last_updated_at,
                           github_url=github_url,
                           **sidebar
                           )


@app.route('/<project>/stats')
def project_stats(project):
    patch_series = patch_report.get_patch_series(project)
    last_updated_at = patch_report.get_last_updated_at(project)

    category_counts = patch_series.get_category_counts()
    author_counts = patch_series.get_author_counts()

    sidebar = _sidebar_for_project(project)

    return render_template('project/stats.html',
                           project=project,
                           category_counts=category_counts,
                           author_counts=author_counts,
                           last_updated_at=last_updated_at,
                           project_tab='Stats',
                           **sidebar
                           )


def _init_app(app):
    app.debug = config.get('web', 'debug')


_init_app(app)


if __name__ == '__main__':
    app.run()
