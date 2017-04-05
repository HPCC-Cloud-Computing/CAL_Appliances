class Cloud(object):
    def __init__(self, type, address, config):
        self.type = type
        self.address = address
        self.config = config
        self.status = 'OK'
        self.get_quota()
        self.get_usage()

    def get_quota(self):
        """Return quota (Unit: GiB)"""
        # TODO:
        # self.quota = connect.head_account()
        #
        pass

    def get_usage(self):
        """Get used (Unit: GiB)"""
        # TODO:
        # self.usage = connect.head_account()
        #
        pass

    def check_health(self):
        pass
