from __future__ import absolute_import
import collections
import datetime
import os
import uuid

from flask import Flask, redirect, render_template, request, url_for
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

import patch_report
from patch_report import cache
from patch_report import config

from patch_report.models.patch_report import get_from_cache


WEB_CONFIG = config.get_section('web')


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


def _common(sidebar_tab, patch_report):
    repos = patch_report.repos

    # Sort sidebar so that repos with most patches are at top
    sidebar_repos = repos[:]
    sidebar_repos.sort(key=lambda p: len(p.patch_series.patches),
                       reverse=True)
    return dict(
            last_updated_at=patch_report.last_updated_at,
            patch_report=patch_report,
            repos=repos,
            sidebar_repos=sidebar_repos,
            sidebar_tab=sidebar_tab,
            stale_data=patch_report.is_data_stale(),
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
                           **_common('Overview', patch_report)
                           )

@app.route('/activity')
def activity():
    try:
        patch_report = get_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    try:
        since_days = int(request.args.get('days', '7'))
    except ValueError:
        since_days = 7

    since = 86400 * (since_days + 1)
    activities = []
    for repo in patch_report.repos:
        repo_activities = repo.get_patch_activities(since)
        activities.extend(repo_activities)

    sort_key = request.args.get('sort_key', 'when')
    sort_dir = request.args.get('sort_dir', 'desc')

    activities.sort(key=lambda a: getattr(a, sort_key),
                    reverse=sort_dir == 'desc')

    return render_template('activity.html',
                           since_days=since_days,
                           activities=activities,
                           sort_dir=sort_dir,
                           sort_key=sort_key,
                           **_common('Activity', patch_report)
                           )


@app.route('/trends')
def trends():
    try:
        patch_report = get_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    def handle_activity(activity, delta_type):
        num_patches[delta_type] += 1
        file_count[delta_type] += activity.patch.file_count
        line_count[delta_type] += activity.patch.line_count

    trend_data = []
    for since_days in (7, 14, 30, 120, 365):
        this_trend = {}
        num_patches = this_trend['num_patches'] = collections.Counter()
        file_count = this_trend['file_count'] = collections.Counter()
        line_count = this_trend['line_count'] = collections.Counter()

        trend_data.append((since_days, this_trend))
        since = 86400 * (since_days + 1)
        for repo in patch_report.repos:
            repo_activities = repo.get_patch_activities(since)
            for activity in repo_activities:
                if activity.what == 'create':
                    handle_activity(activity, 'positive')
                elif activity.what == 'delete':
                    handle_activity(activity, 'negative')

    return render_template('trends.html',
                           trend_data=trend_data,
                           **_common('Trends', patch_report)
                           )


@app.route('/upstream-reviews')
def upstream_reviews():
    try:
        patch_report = get_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    repos = patch_report.repos

    upstream_review_count = 0
    upstream_reviews_by_repo = {}
    for repo in repos:
        upstream_reviews = repo.patch_series.get_upstream_reviews()
        upstream_reviews_by_repo[repo] = upstream_reviews
        upstream_review_count += len(upstream_reviews)

    return render_template('upstream_reviews.html',
                           upstream_reviews_by_repo=upstream_reviews_by_repo,
                           upstream_review_count=upstream_review_count,
                           **_common('Upstream Reviews', patch_report)
                           )


@app.route('/<repo_name>')
def repo_view(repo_name):
    return redirect(url_for('repo_patches', repo_name=repo_name))


def _repo_common(repo, repo_tab, patch_report):
    return dict(
            repo=repo,
            repo_tab=repo_tab,
            **_common(repo.name, patch_report)
            )


@app.route('/<repo_name>/patches')
def repo_patches(repo_name):
    try:
        patch_report = get_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    repo = patch_report.get_repo(repo_name)
    patches = repo.patch_series.patches

    kwargs = _repo_common(repo, 'Patches', patch_report)

    # Category filter
    category_filter = request.args.get('category_filter', None)
    if category_filter:
        if category_filter.lower() == 'none':
            category_filter = None
        patches = filter(lambda p: p.category == category_filter, patches)
        kwargs['category_filter'] = category_filter

    # Sort
    sort_key = request.args.get('sort_key', None)
    if sort_key:
        kwargs['sort_key'] = sort_key
    else:
        sort_key = 'idx'

    sort_dir = request.args.get('sort_dir', None)
    if sort_dir:
        kwargs['sort_dir'] = sort_dir
    else:
        sort_dir = 'desc'

    patches.sort(key=lambda p: getattr(p, sort_key),
                 reverse=sort_dir == 'desc')

    return render_template('repo/patches.html',
                           patches=patches,
                           **kwargs
                           )


@app.route('/<repo_name>/stats')
def repo_stats(repo_name):
    try:
        patch_report = get_from_cache()
    except cache.CacheFileNotFound:
        return _render_empty_cache_page()

    repo = patch_report.get_repo(repo_name)
    patch_series = repo.patch_series
    author_counts = patch_series.get_author_counts()
    category_counts = patch_series.get_category_counts()

    return render_template('repo/stats.html',
                           author_counts=author_counts,
                           category_counts=category_counts,
                           **_repo_common(repo, 'Stats', patch_report)
                           )


def _init_app(app):
    if WEB_CONFIG:
        app.debug = WEB_CONFIG['debug']

    app.config['SECRET_KEY'] = str(uuid.uuid4())
    toolbar = DebugToolbarExtension(app)


_init_app(app)


if __name__ == '__main__':
    app.run()
