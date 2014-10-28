class RemoteRepo(object):
    def __init__(self, name, url, ssh_url):
        self.name = name
        self.url = url
        self.ssh_url = ssh_url
