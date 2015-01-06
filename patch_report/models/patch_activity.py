import os


class PatchActivity(object):
    def __init__(self, repo, commit_hash, when, what, patch,
                 old_filename=None):
        self.repo = repo
        self.commit_hash = commit_hash
        self.when = when
        self.what = what
        self.patch = patch
        self.old_filename = old_filename

    @property
    def url(self):
        return os.path.join(self.repo.html_url, 'commit', self.commit_hash)

    @property
    def filename(self):
        return self.patch.filename

    def __repr__(self):
        if self.what == 'rename':
            return '<PatchActivity %s %s => %s>' % (self.what,
                    self.old_filename, self.filename)
        else:
            return '<PatchActivity %s %s>' % (self.what, self.filename)
