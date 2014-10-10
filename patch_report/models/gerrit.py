class GerritReview(object):
    BASE_URL = "https://review.openstack.org/#q,%s,n,z"

    def __init__(self, change_id):
        self.change_id = change_id

    @property
    def url(self):
        return self.BASE_URL % self.change_id
