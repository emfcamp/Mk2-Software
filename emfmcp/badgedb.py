

class Badge(object):
    def __init__(self, **args):
        self.id = args['id']
        self.hwid = args['hwid']
        self.gwid = args['gwid']

    def toJSON(self):
        # fine until we add weird types to this object
        return self


class BadgeDB(object):
    """Maps 16byte badge hardware IDs to 2byte short IDs."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.cursor = ctx.cursor()
        self.logger = self.ctx.get_logger().bind(origin='BadgeDB')
        self.hw2badge = {}
        self.cursor.execute("SELECT id, hwid, gwid, date FROM badge")
        n = 0
        for row in self.cursor:
            self.hw2badge[row[1]] = Badge(id=row[0], hwid=row[1], gwid=row[2])
            n += 1
        self.logger.info("Loaded %d badge IDs from db" % (n))

    def register(self, hwid, cid, gw_id):
        if hwid in self.hw2badge:
            return self.hw2badge[hwid]

        self.cursor.execute("SELECT id, date, gwid FROM badge WHERE hwid = %s", (hwid,))
        row = self.cursor.fetchone()
        if row:
            (shortid, regdate, existing_gwid) = row
            if existing_gwid != gw_id:
                self.logger("Registering existing badge on new GW", hwid=hwid, old_gw=existing_gwid, new_gw=gw_id)
                self.cursor.execute("UPDATE badge SET gwid = %s WHERE hwid = %s", (gw_id, hwid))
            self.hw2badge[hwid] = Badge(id=shortid, hwid=hwid, gwid=gw_id)
            self.logger.info('badgedb_existing_hwid', hwid=hwid, badgeid=shortid)
        else:
            self.cursor.execute("INSERT INTO badge(hwid,gwid) VALUES(%s,%s) RETURNING id", (hwid, gw_id))
            (shortid) = self.cursor.fetchone()[0]
            self.hw2badge[hwid] = Badge(id=shortid, hwid=hwid, gwid=gw_id)
            self.logger.info('badgedb_issue_newid', hwid=hwid, badgeid=shortid)
        return self.hw2badge[hwid]

    def get_badge_by_id(self, bid):
        """Lookup a Badge() by the 2 byte short id it was assigned"""
        row = self.cursor.execute("SELECT hwid FROM badge WHERE id = %s", (bid)).fetchone()
        if row is None:
            return None
        else:
            (hwid) = row
            return self.get_badge_by_hwid(hwid)

    def get_badge_by_hwid(self, hwid):
        """Lookup a Badge() by the 16 byte badge-hardware id"""
        return self.hw2badge[hwid]

    def get_badges_by_cid(self, cid):
        """Returns a list of all Badge() on a specific connection id (gateway)"""
        for (_hwid, badge) in self.hw2badge:
            if badge.gwid == cid:
                yield badge
