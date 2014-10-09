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


STATE_FILE = os.environ.get('STATE_FILE', 'repo_state.pickle')


@app.route('/')
def index():
    return flask.redirect(flask.url_for('patches'))


@app.route('/patches')
def patches():
    state = patch_report.PatchRepoState(STATE_FILE)
    patch_set = state.load()
    sort_key = flask.request.args.get('sort_key', 'idx')
    sort_dir = flask.request.args.get('sort_dir', 'desc')
    patches = patch_set.get_sorted_patches(sort_key, sort_dir)
    last_updated_at = state.get_last_updated_at()
    return flask.render_template('patches.html',
                                 patches=patches,
                                 sort_key=sort_key,
                                 sort_dir=sort_dir,
                                 last_updated_at=last_updated_at)


if __name__ == '__main__':
    host = os.environ.get('HOST')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)
