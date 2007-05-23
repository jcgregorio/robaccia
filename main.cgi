#!/home/jcgregorio/bin/python2.5
import cgitb; cgitb.enable()
import config
import StringIO
import os
import sys
from wsgiref.handlers import BaseCGIHandler

from urls.main import urls 

try:
    app = urls
    f = StringIO.StringIO("")
    os.environ['PATH_INFO'] = os.environ.get('PATH_INFO', '/')
    if "HEAD" == os.environ['REQUEST_METHOD']:
        os.environ['REQUEST_METHOD'] = "GET"
    BaseCGIHandler(sys.stdin, sys.stdout, f, os.environ).run(app)
    errors = f.getvalue()
    if errors:
        config.log.error(errors)
except:
    import sys
    import traceback
    config.log.error(traceback.format_tb(sys.exc_info()[2]))
    config.log.error(repr(os.environ))
    


