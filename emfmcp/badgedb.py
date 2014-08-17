

class Badge(object):
    def __init__(self, **args):
        for (k, v) in args:
            self.data[k] = v

    def __setattr__(self, k, v):
        self.data[k] = v

    def __setitem__(self, k, v):
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
        self.hw2badge = {}  # map of <16b HW id> --> Badge()
        self.id2hw = {}  # map of <2b short badge id> --> <16b HW id>
        self._id = 1

    def register(self, hwid, cid, gw_id):
        if hwid in self.hw2badge:
            self.logger('badgedb_existing_hwid', hwid=hwid, badgeid=self.hw2badge[hwid].id)
        else:
            badge = Badge(id=self._id, hwid=hwid, gwid=gw_id)
            self.hw2badge[hwid] = badge
            self.id2hw[badge.id] = hwid
            self._id += 1
            self.logger('badgedb_issue_newid', hwid=hwid, badgeid=self.hw2badge[hwid].id)

        return self.hw2badge[hwid]

    def get_badge_by_id(self, bid):
        """Lookup a Badge() by the 2 byte short id it was assigned"""
        if hwid in self.id2hw:
            return self.get_badge_by_hwid(self.id2hw[bid])
        else:
            return None

    def get_badge_by_hwid(self, hwid):
        """Lookup a Badge() by the 16 byte badge-hardware id"""
        if hwid in self.hw2badge:
            return self.hw2badge[hwid]
        else:
            return None
