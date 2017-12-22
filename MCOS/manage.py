#!/usr/bin/env python
# import eventlet
# eventlet.monkey_patch()

from gevent import monkey
monkey.patch_all()

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mcos.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
