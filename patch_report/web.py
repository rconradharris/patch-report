#!/usr/bin/env python
"""
Patch-Repo Web Overview Tool

From command-line run:
    python patch_report/web.py

From webrowser navigate to:
    http://localhost:5000

The following environment variables are used to configure the server:

    HOST: host IP to bind to
    PORT: port to bind to
    DEBUG: enable debug mode
"""
import os

import flask
app = flask.Flask(__name__)
app.debug = os.environ.get('DEBUG') == '1'

import patch_report


@app.route('/')
def index():
    return flask.redirect(flask.url_for('patches'))


@app.route('/patches')
def patches():
    patch_set = patch_report.PatchSet.from_file_refresh_if_not_present(
            STATE_FILE, PATCH_REPO_PATH)

    sort_key = flask.request.args.get('sort_key', 'idx')
    sort_dir = flask.request.args.get('sort_dir', 'desc')
    patches = patch_set.get_sorted_patches(sort_key, sort_dir)
    return flask.render_template('patches.html',
                                 patches=patches,
                                 sort_key=sort_key,
                                 sort_dir=sort_dir)


if __name__ == '__main__':
    PATCH_REPO_PATH = patch_report.get_patch_repo_path()
    STATE_FILE = patch_report.get_state_file()
    host = os.environ.get('HOST')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)
