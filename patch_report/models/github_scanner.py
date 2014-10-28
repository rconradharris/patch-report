from __future__ import absolute_import

from patch_report import cache
from patch_report import config
from patch_report.models.github_endpoint import GithubEndpoint


def get_from_cache():
    return cache.read_file('github_scanner')


def refresh():
    github_scanner = GithubScanner()
    github_scanner.refresh()
    cache.write_file('github_scanner', github_scanner)


class GithubScanner(object):
    def __init__(self):
        self.github_endpoints = []

    @property
    def remote_repos(self):
        remote_repos = []
        for github_endpoint in self.github_endpoints:
            for remote_repo in github_endpoint.remote_repos:
                remote_repos.append(remote_repo)
        return remote_repos

    def refresh(self):
        for username in config.get_github_usernames():
            api_url = config.get_from_multi_section('github', username, 'api_url')
            token = config.get_from_multi_section('github', username, 'token')
            match_string = config.get_from_multi_section(
                    'github', username, 'match_string')

            endpoint = GithubEndpoint(self, username, api_url, token, match_string)
            endpoint.refresh()
            self.github_endpoints.append(endpoint)
