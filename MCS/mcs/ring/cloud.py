class Cloud(object):
    def __init__(self, type, address, config):
        self.type = type
        self.address = address
        self.config = config
        self.status = 'OK'

    def get_quotas(self):
        """Return quota (Unit: GiB)"""
        # TODO:
        # self.quotas = connect.head_account()
        #
        pass

    def get_usage(self):
        """Get used"""
        # TODO:
        # self.usage = connect.head_account()
        #
        pass
