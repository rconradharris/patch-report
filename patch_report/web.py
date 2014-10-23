#!/usr/bin/env python
"""
Patch-Repo Web Overview Tool

From command-line run:
    python patch_report/web.py

From webrowser navigate to:
    http://localhost:5000
"""
import os

import flask
app = flask.Flask(__name__)

import patch_report
from patch_report import config


@app.route('/')
def index():
    project = 'nova'
    return flask.redirect(flask.url_for('project_patches', project=project))


@app.route('/<project>/patches')
def project_patches(project):
    patch_series = patch_report.get_patch_series()

    last_updated_at = patch_report.get_last_updated_at()

    sort_key = flask.request.args.get('sort_key', 'idx')
    sort_dir = flask.request.args.get('sort_dir', 'desc')
    patches = patch_series.get_sorted_patches(sort_key, sort_dir)

    return flask.render_template('patches.html',
                                 patches=patches,
                                 project=project,
                                 sort_key=sort_key,
                                 sort_dir=sort_dir,
                                 last_updated_at=last_updated_at)


@app.route('/<project>/stats')
def project_stats(project):
    patch_series = patch_report.get_patch_series()
    category_counts = patch_series.get_category_counts()
    author_counts = patch_series.get_author_counts()
    return flask.render_template('stats.html',
                                 project=project,
                                 category_counts=category_counts,
                                 author_counts=author_counts)


def _init_app(app):
    app.debug = config.get('web', 'debug')


_init_app(app)


if __name__ == '__main__':
    app.run()
