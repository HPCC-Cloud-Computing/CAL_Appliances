import csv
import os
import sys

import psutil
from pympler import muppy
from pympler import summary
from pympler.asizeof import asizeof

THRESHOLD = 2 * 1024 * 1024


class MemoryWithPsutilMiddleware(object):
    def process_request(self, request):
        request._mem = psutil.Process(os.getpid()).memory_info()

    def process_response(self, request, response):
        mem = psutil.Process(os.getpid()).memory_info()
        if hasattr(request, '_mem'):
            diff = mem.rss - request._mem.rss
            with open('mem_log.csv', 'ab') as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                writer.writerow([str(diff), request.path])
            # if diff > THRESHOLD:
            #    print >> sys.stderr, 'MEMORY USAGE %r' %\
            #     ((diff, request.path),)
        return response


def output_function(o):
    return str(type(o))


class MemoryWithPymplerMiddleware(object):
    """
    Measure memory taken by requested view, and response
    """

    def __init__(self):
        self.start_objects = None

    def process_request(self, request):
        req = request.META['PATH_INFO']
        if req.find('site_media') == -1:
            self.start_objects = muppy.get_objects()

    def process_response(self, request, response):
        req = request.META['PATH_INFO']
        if req.find('site_media') == -1 and self.start_objects:
            print req
            self.end_objects = muppy.get_objects()
            sum_start = summary.summarize(self.start_objects)
            sum_end = summary.summarize(self.end_objects)
            diff = summary.get_diff(sum_start, sum_end)
            summary.print_(diff)
            print '~~~~~~~~~'
            a = asizeof(response)
            print 'Total size of response object in kB: %s' % str(a / 1024.0)
            print '~~~~~~~~~'
            a = asizeof(self.end_objects)
            print 'Total size of end_objects in MB: %s' % str(a / 1048576.0)
            b = asizeof(self.start_objects)
            print 'Total size of start_objects in MB: %s' % str(b / 1048576.0)
            print '~~~~~~~~~'
        return response
