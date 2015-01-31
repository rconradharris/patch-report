from __future__ import absolute_import

from github import Github

from patch_report import cache
from patch_report import config
from patch_report.simplelog import log
from patch_report import state


class RemoteRepo(object):
    def __init__(self, name, url, ssh_url, html_url):
        self.name = name
        self.url = url
        self.ssh_url = ssh_url
        self.html_url = html_url

    @classmethod
    def discover(cls):
        discovered_repos = []

        for username in config.get_github_usernames():
            api_url = config.get_from_multi_section('github', username, 'api_url')
            token = config.get_from_multi_section('github', username, 'token')
            match_string = config.get_from_multi_section(
                    'github', username, 'match_string')

            user = Github(token, base_url=api_url).get_user(username)
            for github_repo in user.get_repos():
                if match_string in github_repo.name:
                    log("Discovered remote repo %s" % github_repo.name)
                    name = github_repo.name.replace(match_string, '')
                    remote_repo = RemoteRepo(name,
                                             github_repo.url,
                                             github_repo.ssh_url,
                                             github_repo.html_url)
                    discovered_repos.append(remote_repo)

        cache.write_file('discovered_repos', discovered_repos)

    @classmethod
    def _get_all(cls):
        return cache.read_file('discovered_repos')

    @classmethod
    def get_all(cls):
        try:
            return cls._get_all()
        except state.FileNotFound:
            cls.discover()
            return cls._get_all()
