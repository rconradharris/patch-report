def get_from_line(patch, line):
    if 'Upstream-Change-Id' not in line:
        return

    change_id = line.split(' ', 1)[1].strip()
    return GerritReview(patch, change_id)


class GerritReview(object):
    BASE_URL = "https://review.openstack.org/#q,%s,n,z"

    def __init__(self, patch, change_id):
        self.patch = patch
        self.change_id = change_id

    @property
    def label(self):
        return self.change_id[:5]

    @property
    def url(self):
        return self.BASE_URL % self.change_id
