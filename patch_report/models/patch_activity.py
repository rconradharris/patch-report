class PatchActivity(object):
    def __init__(self, repo, when, what, patch, old_filename=None):
        self.repo = repo
        self.when = when
        self.what = what
        self.patch = patch
        self.old_filename = old_filename

    def __repr__(self):
        if self.what == 'rename':
            return '<PatchActivity %s %s => %s>' % (self.what,
                    self.old_filename, self.patch.filename)
        else:
            return '<PatchActivity %s %s>' % (self.what, self.patch.filename)
