

class Badge(object):
    def __init__(self, **args):
        for (k, v) in args:
            self.data[k] = v

    def __getattr__(self, k):
        return self.data[k]

    def __getitem__(self, k):
        return self.data[k]


class BadgeDB(object):
    """Maps 16byte badge hardware IDs to 2byte short IDs."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = self.ctx.get_logger().bind(origin='BadgeDB')
        self.db = {}
        self._id = 1

    def register(self, hwid, cid, gw_id):
        if hwid in self.db:
            self.logger('badgedb_existing_hwid', hwid=hwid, badgeid=self.db[hwid].id)
        else:
            badge = Badge(self._id, hwid=hwid, id=self._id)
            self.db[hwid] = badge
            self._id += 1
            self.logger('badgedb_issue_newid', hwid=hwid, badgeid=self.db[hwid].id)

        return self.db[hwid]

    def lookup(self, hwid):
        if hwid in self.db:
            return self.db[hwid]
        else:
            return None
