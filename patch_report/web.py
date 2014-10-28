from __future__ import absolute_import
import datetime
import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

import patch_report
from patch_report import cache
from patch_report import config

from patch_report.models.patch_report import get_from_cache


@app.template_filter('pluralize')
def pluralize(singular, count, plural=None):
    if count == 1:
        return singular

    if not plural:
        plural = singular + 's'

    return plural


@app.template_filter('time_ago_in_words')
def time_ago_in_words(from_time):
    if not from_time:
        return 'never'

    utcnow = datetime.datetime.utcnow()
    timedelta = utcnow - from_time
    secs = timedelta.seconds
    days = timedelta.days

    if days >= 730:
        return '%s years ago' % (days / 365)
    elif days >= 360:
        return 'last year'
    elif days >= 31:
        return "%s months ago" % (days / 30)
    elif days >= 14:
        return "%s weeks ago" % (days / 7)
    elif days >= 7:
        return "last week"
    elif days > 1:
        return "%s days ago" % days
    elif days == 1:
        return "yesterday"
    elif secs >= 7200:
        return "%s hours ago" % (secs / 3600)
    elif secs >= 3600:
        return "an hour ago"
    elif secs >= 120:
        return "%s minutes ago" % (secs / 60)
    elif secs >= 60:
        return 'a minute ago'
    else:
        return 'just now'


def _render_empty_cache_page():
    return render_template('empty_cache.html')


def _common(sidebar_tab, repos):
    # Sort sidebar so that repos with most patches are at top
    sidebar_repos = repos[:]
    sidebar_repos.sort(key=lambda p: len(p.patch_series.patches),
                       reverse=True)
    return dict(
            repos=repos,
            sidebar_repos=sidebar_repos,
            sidebar_tab=sidebar_tab,
            stale_data=repos[0].is_data_stale(),
            )


@app.route('/')
def overview():
    try:
        patch_report = get_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    repos = patch_report.repos

    overview_counts_by_repo = {}
    for repo in repos:
        overview_counts = repo.patch_series.get_overview_counts()
        overview_counts_by_repo[repo] = overview_counts

    sort_key = request.args.get('sort_key', 'num_patches')
    sort_dir = request.args.get('sort_dir', 'desc')
    sorted_repos = sorted(repos,
        key=lambda p: overview_counts_by_repo[p][sort_key],
        reverse=sort_dir == 'desc')

    return render_template('overview.html',
                           overview_counts_by_repo=overview_counts_by_repo,
                           sort_key=sort_key,
                           sort_dir=sort_dir,
                           sorted_repos=sorted_repos,
                           **_common('Overview', repos)
                           )


@app.route('/upstream-reviews')
def upstream_reviews():
    try:
        patch_report = get_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    repos = patch_report.repos

    upstream_reviews_by_repo = {}
    for repo in repos:
        upstream_reviews = repo.patch_series.get_upstream_reviews()
        upstream_reviews_by_repo[repo] = upstream_reviews

    return render_template('upstream_reviews.html',
                           upstream_reviews_by_repo=upstream_reviews_by_repo,
                           **_common('Upstream Reviews', repos)
                           )


@app.route('/<project_name>')
def project_view(project_name):
    return redirect(url_for('project_patches', project_name=project_name))


def _repo_common(repo, repo_tab):
    patch_report = get_from_cache()
    repos = patch_report.repos
    return dict(
            repo=repo,
            repo_tab=repo_tab,
            **_common(repo.name, repos)
            )


@app.route('/<project_name>/patches')
def project_patches(project_name):
    try:
        patch_report = get_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    repo = patch_report.get_repo(project_name)
    sort_key = request.args.get('sort_key', 'idx')
    sort_dir = request.args.get('sort_dir', 'desc')
    patches = repo.patch_series.get_sorted_patches(sort_key, sort_dir)

    return render_template('project/patches.html',
                           patches=patches,
                           sort_dir=sort_dir,
                           sort_key=sort_key,
                           **_repo_common(repo, 'Patches')
                           )


@app.route('/<project_name>/stats')
def project_stats(project_name):
    try:
        patch_report = get_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    repo = patch_report.get_repo(project_name)
    patch_series = repo.patch_series
    author_counts = patch_series.get_author_counts()
    category_counts = patch_series.get_category_counts()

    return render_template('project/stats.html',
                           author_counts=author_counts,
                           category_counts=category_counts,
                           **_repo_common(repo, 'Stats')
                           )


def _init_app(app):
    app.debug = config.get('web', 'debug')


_init_app(app)


if __name__ == '__main__':
    app.run()
