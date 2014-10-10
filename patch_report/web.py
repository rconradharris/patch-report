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
    return flask.redirect(flask.url_for('patches'))


@app.route('/patches')
def patches():
    patch_series = patch_report.get_patch_series()

    last_updated_at = patch_report.get_last_updated_at()

    sort_key = flask.request.args.get('sort_key', 'idx')
    sort_dir = flask.request.args.get('sort_dir', 'desc')
    patches = patch_series.get_sorted_patches(sort_key, sort_dir)

    return flask.render_template('patches.html',
                                 patches=patches,
                                 sort_key=sort_key,
                                 sort_dir=sort_dir,
                                 last_updated_at=last_updated_at)


def _init_app(app):
    app.debug = config.get('web', 'debug')


_init_app(app)


if __name__ == '__main__':
    app.run()
