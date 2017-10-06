import subprocess


def start_periodic_check__clusters_status():
    print "Start execute periodic_check__clusters_status sub process"
    proc = subprocess.Popen(["../mcos_venv/bin/python",
                             "mcos/sub_processes/"
                             "periodic_check_clusters_status.py"])
    print "Continue process main process"
    return proc.pid


def start_periodic_send_cluster_status():
    print "Start execute sub process"
    proc = subprocess.Popen(["../mcos_venv/bin/python",
                             "mcos/sub_processes/"
                             "periodic_send_cluster_status.py"])
    print "Continue process main process"
    return proc.pid


def start_handle_cluster_msg_server():
    print "Start handle cluster message celery server"
    celery_cmdline = '../mcos_venv/bin/celery worker -A ' \
                     'mcos_celery_server -l INFO'.split(" ")

    proc = subprocess.Popen(celery_cmdline)
    print "Continue process main process"
    return proc.pid