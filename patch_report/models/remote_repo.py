from __future__ import absolute_import


class RemoteRepo(object):
    def __init__(self, name, url, ssh_url, html_url):
        self.name = name
        self.url = url
        self.ssh_url = ssh_url
        self.html_url = html_url
