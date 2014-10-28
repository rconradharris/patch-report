from __future__ import absolute_import
from github import Github

from patch_report.models.remote_repo import RemoteRepo


class GithubEndpoint(object):
    def __init__(self, scanner, username, api_url, token, match_string):
        self.scanner = scanner
        self.username = username
        self.api_url = api_url
        self.token = token
        self.match_string = match_string
        self.remote_repos = []

    def refresh(self):
        gh = Github(self.token, base_url=self.api_url)
        user = gh.get_user(self.username)
        for github_repo in user.get_repos():
            if self.match_string in github_repo.name:
                print "Detected remote repo %s" % github_repo.name
                name = github_repo.name.replace(self.match_string, '')
                remote_repo = RemoteRepo(name,
                                         github_repo.url,
                                         github_repo.ssh_url,
                                         github_repo.html_url)
                self.remote_repos.append(remote_repo)
