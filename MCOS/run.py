"""
WSGI config for mcos project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""
import time
import os
import subprocess
from sys import path
from os.path import abspath, dirname
import os
import signal

path.insert(0, os.getcwd())
from mcos.sub_processes import manage as sub_procs_manage


def kill_child(sub_procs):
    for sub_proc_id in sub_procs:
        os.kill(sub_proc_id, signal.SIGTERM)
    print("done")


if __name__ == "__main__":
    mcos_celery_server_proc_id = \
        sub_procs_manage.start_handle_cluster_msg_server()
    send_cluster_status_proc_id = \
        sub_procs_manage.start_periodic_send_cluster_status()
    check_cluster_status_proc_id = \
        sub_procs_manage.start_periodic_check__clusters_status()
    ring_periodic_update_proc_id = \
        sub_procs_manage.start_ring_periodic_update_proc()
    data_sync_proc_id = \
        sub_procs_manage.start_data_sync_proc()

    import atexit

    atexit.register(kill_child, [
        mcos_celery_server_proc_id,
        send_cluster_status_proc_id,
        check_cluster_status_proc_id,
        ring_periodic_update_proc_id,
        data_sync_proc_id
    ])

    from mcos import wsgi
    from sys import path

    wsgi.setup_system_and_start_servers()
