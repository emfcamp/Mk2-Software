

class Badge(object):
    def __init__(self, **args):
        self.id=args['id']
        self.hwid=args['hwid']
        self.gwid=args['gwid']

    def toJSON(self):
        # fine until we add weird types to this object
        return self


class BadgeDB(object):
    """Maps 16byte badge hardware IDs to 2byte short IDs."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.logger = self.ctx.get_logger().bind(origin='BadgeDB')
        self.hw2badge = {}  # map of <16b HW id> --> Badge()
        self.id2hw = {}  # map of <2b short badge id> --> <16b HW id>
        self.cid2hw = {}  # map of cid -> [hwid1, hwid2..]
        self._id = 1

    def register(self, hwid, cid, gw_id):
        if hwid in self.hw2badge:
            self.logger.info('badgedb_existing_hwid', hwid=hwid, badgeid=self.hw2badge[hwid].id)
        else:
            badge = Badge(id=self._id, hwid=hwid, gwid=gw_id)
            self.hw2badge[hwid] = badge
            self.id2hw[badge.id] = hwid
            if gw_id not in self.cid2hw:
                self.cid2hw[gw_id] = [hwid]
            else:
                self.cid2hw[gw_id].push(hwid)
            self._id += 1
            self.logger.info('badgedb_issue_newid', hwid=hwid, badgeid=self.hw2badge[hwid].id)

        return self.hw2badge[hwid]

    def get_badge_by_id(self, bid):
        """Lookup a Badge() by the 2 byte short id it was assigned"""
        if bid in self.id2hw:
            return self.get_badge_by_hwid(self.id2hw[bid])
        else:
            return None

    def get_badge_by_hwid(self, hwid):
        """Lookup a Badge() by the 16 byte badge-hardware id"""
        if hwid in self.hw2badge:
            return self.hw2badge[hwid]
        else:
            return None

    def get_badges_by_cid(self, cid):
        """Returns a list of all Badge() on a specific connection id (gateway)"""
        if cid not in self.cid2hw:
            return {}
        ret = {}
        for hwid in self.cid2hw[cid]:
            if hwid in self.hw2badge:
                badge = self.hw2badge[hwid]
                ret[badge.id] = badge.toJSON()
        return ret
