import os
import logging
import logging.handlers
import mimeparse
import md5
from genshi.template import TemplateLoader
from cgi import parse_qs
import StringIO

TEMPLATE_DIRS = ["templates"]

def genshi_templater(template_dir_paths, template_file, vars, serialization):
    loader = TemplateLoader(template_dir_paths)
    tmpl = loader.load(template_file)
    stream = tmpl.generate(**vars)
    body = stream.render(method=serialization)
    return body

def simplejson_templater(template_dir_paths, template_file, vars, serialization):
    import simplejson
    return simplejson.dumps(vars)

extensions = {
    'html': ('text/html; charset=utf-8', 'html', genshi_templater),
    'atom': ('application/atom+xml; charset=utf-8', 'xml', genshi_templater),
    'svc': ('application/atomsvc+xml; charset=utf-8', 'xml', genshi_templater),
    'json': ('application/json', 'json', simplejson_templater)
}

def find_template(template_file):
    for dir in TEMPLATE_DIRS:
        full_name = os.path.join(dir, template_file)
        if os.path.exists(full_name) and os.path.isfile(full_name):
            return full_name
    return None

def etag_from_raw_etag(raw_etag, template_file):
    file = find_template(template_file)
    if file:
        last_modified = str(os.stat(file).st_mtime)
        hash = md5.new(raw_etag)
        hash.update(last_modified)
        return '"%s"' % hash.hexdigest()
    return None
 
def render(environ, start_response, template_file, vars, headers={}, status="200 Ok", raw_etag=None):
    if raw_etag:
        etag = etag_from_raw_etag(raw_etag, template_file)
        headers['etag'] = etag    
        if etag == environ.get('HTTP_IF_NONE_MATCH', ''):
            return http304(environ, start_response)

    (contenttype, serialization, templater) = ('text/html; charset=utf-8', 'html', genshi_templater)
    ext = template_file.rsplit(".")
    if len(ext) > 1 and (ext[1] in extensions):
        (contenttype, serialization, templater) = extensions[ext[1]]
   
    body = templater(TEMPLATE_DIRS, template_file, vars, serialization)

    if 'content-type' not in headers:
        headers['content-type'] = contenttype
    start_response(status, list(headers.iteritems()))
    return [body]

def form_parser(environ):
    """Parses the incoming x-www-form-urlencoded data into a dictionary"""
    return dict([(key, "".join(value)) for key, value in environ['formpostdata'].iteritems()])

def json_parser(environ):
    import simplejson
    size = int(environ.get('CONTENT_LENGTH', "-1"))
    if size > 0:
        return simplejson.loads(environ['wsgi.input'].read(size)) 
    else:
        return {}

def deferred_collection(environ, start_response):
    """Look for a views.* module to handle this incoming
    request. Presumes the module has 
    an 'app' that is a WSGI application."""
    # Pull out the view name from the template parameters
    view = environ['wsgiorg.routing_args'][1]['view']
    # Load the named view from the 'views' directory
    m = __import__("views." + view, globals(), locals())
    # Pass along the WSGI call into the given application
    logging.getLogger('robaccia').debug("View: %s" % view)
    return getattr(getattr(m, view), 'app')(environ, start_response)

def render_json(start_response, struct):
    import simplejson
    body = simplejson.dumps(struct)
    start_response("200 OK", [('Content-Type', 'text/plain')])
    return [body]

def http200(environ, start_response):
    logging.getLogger('robaccia').info("200: %s" % environ.get('PATH_INFO', ''))
    start_response("200 Ok", [])
    return []

def http404(environ, start_response):
    logging.getLogger('robaccia').warning("404: %s" % environ.get('PATH_INFO', ''))
    start_response("404 Not Found", [('Content-Type', "text/html")])
    return ["<h1>File Not Found</h1>"]

def http304(environ, start_response):
    logging.getLogger('robaccia').info("304: %s" % environ.get('PATH_INFO', ''))
    start_response("304 Not Modified", [])
    return []

def http303(environ, start_response, location):
    logging.getLogger('robaccia').info("303: %s" % environ.get('PATH_INFO', ''))
    start_response("303 See Other", [('location', location)])
    return []

def http405(environ, start_response):
    logging.getLogger('robaccia').info("405: %s" % environ.get('PATH_INFO', ''))
    start_response("405 Method Not Allowed", [('Content-Type', "text/html")])
    return ["<h1>That action is not allowed on this resource.</h1>"]

def http403(environ, start_response):
    logging.getLogger('robaccia').info("403: %s" % environ.get('PATH_INFO', ''))
    start_response("403 Forbidden", [('Content-Type', "text/html")])
    return ["<h1>You are unauthorized to modify that resource.</h1>"]

def http415(environ, start_response, message="The server is refusing to service the request because the entity of the request is in a format not supported by the requested resource for the requested method."):
    logging.getLogger('robaccia').info("415: %s" % environ.get('PATH_INFO', ''))
    start_response("415 Unsupported Media Type", [('Content-Type', "text/html")])
    return [message]


LOG_PATH = "log"
def init_logging():
    if os.path.exists(LOG_PATH) and os.path.isdir(LOG_PATH):
        logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        filename='last',
        filemode='a')

        detail_handler = logging.handlers.RotatingFileHandler(os.path.join(LOG_PATH, "detail.log"), "a", 100000, 5)
        detail_handler.setLevel(logging.DEBUG)
        detail_handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)-8s %(message)s'))
        logdetail = logging.getLogger('robaccia')
        logdetail.addHandler(detail_handler)

        request_handler = logging.handlers.RotatingFileHandler(os.path.join(LOG_PATH, "request.log"), "a", 100000, 5)
        request_handler.setLevel(logging.INFO)
        request_handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)-8s %(message)s'))
        logrequest = logging.getLogger('robaccia.request')
        logrequest.addHandler(request_handler)

