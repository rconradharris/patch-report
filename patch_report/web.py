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
    pr = patch_report.PatchReport.load()
    last_updated_at = patch_report.PatchReport.get_last_updated_at()

    sort_key = flask.request.args.get('sort_key', 'idx')
    sort_dir = flask.request.args.get('sort_dir', 'desc')
    patches = pr.get_sorted_patches(sort_key, sort_dir)

    return flask.render_template('patches.html',
                                 patches=patches,
                                 sort_key=sort_key,
                                 sort_dir=sort_dir,
                                 last_updated_at=last_updated_at)

if __name__ == '__main__':
    app.debug = config.get('web', 'debug')
    app.run(host=config.get('web', 'host'),
            port=config.get('web', 'port'))
