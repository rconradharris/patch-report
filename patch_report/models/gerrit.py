def get_from_line(line):
    if 'Upstream-Change-Id' not in line:
        return

    change_id = line.split(' ', 1)[1].strip()
    return GerritReview(change_id)


class GerritReview(object):
    BASE_URL = "https://review.openstack.org/#q,%s,n,z"

    def __init__(self, change_id):
        self.change_id = change_id

    @property
    def url(self):
        return self.BASE_URL % self.change_id
