"""
WSGI Dispatcher

Dispatcher is WSGI middleware that dispatches incoming WSGI
requests based on URI Templates and the request method and 
passes along the request to the selected WSGI application.
Dispatcher conforms to the routing_args_ specification.
You should read PEP333_ if you don't know about WSGI.

Dispatcher maps an incoming HTTP request path against a
series of patterns. Patterns may be given as plain text
string that must match the request path exactly, they may
be templates, or they may be specified as regular expressions. 
Groups of matching characters for templates and regular expressions
are extracted from the URI for easy handling by your application.
When a match is obtained then that
matching WSGI application is given the request to handle.::

    from wsgidispatcher import Dispatcher

    def index(environ, start_response):
        start_response("200 Ok", [('content-type', 'text/html')])
        return ['<h1>"Hi there</h1>']

    def hello(environ, start_response):
        response = "<h1>Hello %s</h1>" % environ['wsgiorg.routing_args'][1]['name']
        start_response("200 Ok", [('content-type', 'text/html')])
        return [response]

    urls = Dispatcher()
    urls.add('/index/', GET=index)
    urls.add('/index/{name}', GET=hello)

    from wsgiref.simple_server import make_server

    server = make_server('', 8000, urls)
    server.serve_forever()

If you save this off as ``dispatcher-example.py`` and 
run it from the command line::

    $ python dispatcher-example.py

you can then visit this URI::

    http://localhost:8000/index/Joe

And you will get a web page that prints 'Hello Joe'.

If you visit this URI::

    http://localhost:8000/index/

You will get a web page that prints 'Hi there'.

Note that wsgiref is standard in Python 2.5.

Look at the function ``hello()``, it uses the data stored
in 'wsgiorg.routing_args' to determine the value of the
'{id}' segment of the requested URI.

Some things to note:

* Patterns are matched in the order in which they are added to the Dispatcher.
* First match wins
* You can define you own new ranges, or over-ride the built in ranges. 
* You can provide one application for every method, or you can
  provide a single application that will response to every method used.
* If no matches are found a 404 message is generated. 
* You can provide your own custom 404 handler.
* Does not use setuptools
* No external dependencies

You specify an application to handle a request based on the
HTTP method::

    urls = Dispatcher()
    urls.add('/index/', GET=index, POST=add_stuff)
    urls.add('/index/{name}', GET=hello)

For applications that will handle all methods, you can either
use _ANY_ for the method, or drop the method entirely::

    urls = Dispatcher()
    urls.add('/index/', does_it_all_app)
    urls.add('/index/{name}', GET=hello)

You can also mix and match templates and regular expressions::

    urls = Dispatcher()
    urls.add('/index/', does_it_all_app)
    urls.addregex('^/comments/(\d+)$', GET=comments)
    urls.add('/index/{name}', GET=hello)

You can add an optional range qualifier to every template
parameter that restricts the characters that consistitute
a match. The range specifier follows a colon in the template name.
Here are the ranges that are predefined:

+-----------+--------------------+
|Range      |Regular Expression  |
+===========+====================+
|word       |\w+                 | 
+-----------+--------------------+
|alpha      |[a-zA-Z]+           |
+-----------+--------------------+
|digits     |\d+                 |
+-----------+--------------------+
|alnum      |[a-zA-Z0-9]+        |
+-----------+--------------------+
|segment    |[^/]+               |
+-----------+--------------------+
|unreserved |[a-zA-Z\d\-\.\_\~]+ |
+-----------+--------------------+
|any        |.+                  |
+-----------+--------------------+

Here is an example the uses ranges::

    d = Dispatcher()
    d.add("/a/b/{n:digits}", myapp)

You can add new range values by passing in a dictionary that
maps the range name to a regular expression. Here is an example
of a Dispatcher being constructed that recognizes real numbers in
engineering format::

 d = Dispatcher(ranges = {'real':'(\+|-)?[1-9]\.[0-9]*E(\+|-)?[0-9]+'})
 d.add("/a/b/{n:real}", my_math_app)

Templates understand three special kinds of markup:

+--------+-------------------------------------------------------------------------------------------------------------------+
| {name} | Whatever matches this part of the path will be available to the application in the routing_args named parameters. | 
+--------+-------------------------------------------------------------------------------------------------------------------+
| []     | Any part of a path enclosed in brackets is optional                                                               |
+--------+-------------------------------------------------------------------------------------------------------------------+ 
| \|     | The bar may only be present at the end of the template and signals that the path need not match the whole path.   |
+--------+-------------------------------------------------------------------------------------------------------------------+

* Brackets may be nested
* Brackets may contain template parameters

This is an exmaple template::

    /service/[{collection:alpha}[/[{id:unreserved}/]]][;{noun}]

The template will match these paths::

    /service;service_document
    /service/entry/12/;media
    /service/

But not these::

    /service
    /service/12/entry/;media
    /other/

In addition, regular expressions may be used as templates.
They are added via ``addregex()``::

    d = Dispatcher()
    d.addregex("/([^/]+)/(?P<fred>\d+)", self._app)
    d({'PATH_INFO': '/fred/123abc', 'REQUEST_METHOD': 'GET'}, self._start_response)
    self.assertEqual(self.environ['wsgiorg.routing_args'][0][0], 'fred')
    self.assertEqual(self.environ['wsgiorg.routing_args'][1]['fred'], '123')

Note that the value of the unnamed groups is returned in the positional args
and the named groups are returned via the named args.

.. _PEP333: http://www.python.org/dev/peps/pep-0333/
.. _routing_args: http://wsgi.org/wsgi/Specifications/routing_args           
"""

__version__ = "0.1.0"
__author__ = "Joe Gregorio <http://bitworking.org>"
__license__ = """MIT  
Copyright (c) 2007, Joe Gregorio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE."""

__all__ = [ 
    "DispatcherException",
    "DuplicateArgumentError",       
    "InvalidArgumentError",   
    "InvalidTemplateError",
    "Dispatcher",
    "template2regex"
]
    
import re
import logging

logger = logging.getLogger("robaccia.request")

NOMATCH = -1
template_splitter = re.compile("([\[\]\{\}])")

class DispatcherException(Exception): pass
class DuplicateArgumentError(DispatcherException): pass 
class InvalidArgumentError(DispatcherException): pass
class InvalidTemplateError(DispatcherException): pass

DEFAULT_RANGES = {
        'word': r'\w+', 
        'alpha': r'[a-zA-Z]+',
        'digits': r'\d+',
        'alnum': r'[a-zA-Z0-9]+',
        'segment': r'[^/]+',
        'unreserved': r'[a-zA-Z\d\-\.\_\~]+',
        'any': r'.+'
        }

# The conversion done in template2regex can be in one of two states, either
# handling a path, or it can be inside a {} template.
S_PATH = 0
S_TEMPLATE = 1 

def template2regex(template, ranges=None):
    """
    Converts a template, such as /{name}/ to 
    a regular expression, e.g.  /(?P<name>[^/]+)/
    Ranges are given after a colon in a template name
    to indicate a restriction on the characters that
    can appear there. For example, in the template::

        "/user/{id:alpha}"

    The ``id`` must contain only characters from a-zA-Z.
    Other characters there will cause the pattern not to match.

    The ranges parameter is an optional dictionary that maps
    range names to regular expressions. New range names
    can be added, or old range names can be redefined 
    using this parameter.

    Example:

        >>> import wsgidispatcher
        >>> wsgidispatcher.template2regex("{fred}")
        '^(?P<fred>[^/]+)$'

    This function is used internally by Dispatcher, but left
    public for testing and in case anyone finds it useful.
    """
    if ranges == None:
        ranges = DEFAULT_RANGES
    anchor = True
    state = S_PATH
    if len(template) and template[-1] == '|':
        anchor = False

    bracketdepth = 0 
    result = ['^']
    name = "" 
    pattern = "[^/]+"
    rangename = None
    for c in template_splitter.split(template):
        if state == S_PATH:
            if len(c) > 1:
                result.append(c)
            elif c == '[':
                result.append("(")
                bracketdepth += 1
            elif c == ']':
                bracketdepth -= 1
                if bracketdepth < 0:
                    raise InvalidTemplateError("Mismatched brackets in %s" % template)
                result.append(")?")
            elif c == '{':
                name = ""
                state = S_TEMPLATE
            elif c == '}':
                raise InvalidTemplateError("Mismatched braces in %s" % template)
            elif c == '|':
                pass
            else:
                result.append(c)
        else:
            if c == '}':
                if rangename and rangename in ranges:
                    result.append("(?P<%s>%s)" % (name, ranges[rangename]))
                else:
                    result.append("(?P<%s>%s)" % (name, pattern))
                state = S_PATH
                rangename = None
            else:
                name = c
                if name.find(":") > -1:
                    name, rangename  = name.split(":")
    if bracketdepth != 0:
        raise InvalidTemplateError("Mismatched brackets in %s" % template)
    if state == S_TEMPLATE:
        raise InvalidTemplateError("Mismatched braces in %s" % template)
    if anchor:
        result.append('$')
    return "".join(result)


class TemplatePredicate(object):
    """The presence of [], |, or {} indicates 
    match is a template and not just a plain string match."""
    def __init__(self, path, appdict, ranges):
        self.path = path
        self.appdict = appdict
        self.ranges = ranges

        # We lazy eval the paths, only parsing regex's and such until we are called on to make a match.
        self.isparsed = False

        # Either this is a template, or a pure string match
        self.istemplate = False

    def __call__(self, environ, start_response):
        if not self.isparsed:
            if self.path.find("{") > -1 or self.path.find("[") > -1 or (len(self.path) and self.path[-1] == '|'):
                regex = template2regex(self.path, self.ranges)
                try:
                    self.regex= re.compile(regex)
                except:
                    raise Exception("Invalid Template")
                self.istemplate = True
                self.isparsed = True
            else:
                self.isparsed = True
        request_path = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', 'GET')
        if not self.istemplate:
            if self.path == request_path:
                if method in self.appdict or "_ANY_" in self.appdict:
                    environ['wsgiorg.routing_args'] = ([], {})
                    return self.appdict.get(method, self.appdict.get('_ANY_', None))(environ, start_response)
        else:
            script_name = environ.get('SCRIPT_NAME', '')
            match = self.regex.match(request_path)
            if match:
                if method in self.appdict or "_ANY_" in self.appdict:
                    extra_request_path = request_path[match.end():]
                    pos, named = environ.get('wsgiorg.routing_args', ((), {}))
                    new_named = named.copy()
                    new_named.update(match.groupdict())
                    environ['wsgiorg.routing_args'] = (pos, new_named)
                    environ['SCRIPT_NAME'] = script_name + request_path[:match.end()]
                    environ['PATH_INFO'] = extra_request_path
                    return self.appdict.get(method, self.appdict.get('_ANY_', None))(environ, start_response)
        return NOMATCH


class RegexPredicate(object):
    def __init__(self, regex, appdict, ranges):
        self.regexsrc = regex 
        self.isparsed = False
        self.appdict = appdict

    def __call__(self, environ, start_response):
        if not self.isparsed:
            self.regex = re.compile(self.regexsrc)
        script_name = environ.get('SCRIPT_NAME', '')
        request_path = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', 'GET')
        match = self.regex.match(request_path)
        if match:
            extra_request_path = request_path[match.end():]
            pos, named = environ.get('wsgiorg.routing_args', ((), {}))
            new_named = named.copy()
            new_named.update(match.groupdict())
            new_pos = list(pos) + list(match.groups())
            environ['wsgiorg.routing_args'] = (new_pos, new_named)
            environ['SCRIPT_NAME'] = script_name + request_path[:match.end()]
            environ['PATH_INFO'] = extra_request_path
            environ['wsgiorg.routing_args']= (list(match.groups()), match.groupdict())
            if method in self.appdict or "_ANY_" in self.appdict:
                return self.appdict.get(method, self.appdict.get('_ANY_', None))(environ, start_response)
        return NOMATCH


class Dispatcher(object):

    def __init__(self, handle404 = None, ranges = None):
        """
handle404 - A WSGI application to be used when no match is found for a requested URI path.

ranges - A dictionary that maps new range names to regular expressions that match those characters. 

Example::
    import logging 

    def my404(environ, start_response):
        logging.warning("404: %s" % environ.get('PATH_INFO', ''))
        start_response("404 Not Found", [('Content-Type', "text/html")])
        return ["<h1>File Not Found</h1>"]
    
    d = Dispatcher(self.my404, {'real':'(\+|-)?[1-9]\.[0-9]*E(\+|-)?[0-9]+'})
    d.add("/arc/{degrees:real}/", view.display)

        """
        self.matchers = []
        if handle404 == None:
            self.handle404 = self._404 
        else:
            self.handle404 = handle404
        self.ranges = DEFAULT_RANGES 
        if ranges:
            self.ranges.update(ranges)

    def _404(self, environ, start_response):
        """ The default 404 response for Dispatcher. You can pass in your
        own app to handle 404s to __init__."""
        start_response("404 Not Found", [('Content-Type', "text/html")])
        return ["<h1>File Not Found</h1>"]

    def __call__(self, environ, start_response):
        """An instance of a Dispatcher is a callable that is
        a WSGI application. See the module level documentation
        for an example."""
        logger.info(environ.get('PATH_INFO', '-no path given-'))
        for predicate in self.matchers:
            ret = predicate(environ, start_response)
            if ret != NOMATCH:
                return ret
        return self.handle404(environ, start_response)

    def _appmap(self, args, kwargs):
        appmap = {}
        if args and kwargs: 
            raise DuplicateArgumentError("You can not specify both an application and a map of methods")
        if args:
            if len(args) != 1:
                raise InvalidArgumentError("You may only specify one WSGI app for each _ANY_ call.")
            appmap['_ANY_'] = args[0]
        else:
            appmap.update(kwargs)
        return appmap

    def add(self, path, *args, **kwargs):
        """You can either add a WSGI application to handle all the matches,
        or you can add applications based on the method. 

        Example::
            d = Dispatcher()
            d.add("/fred/", app)
            d.add("/barney/", GET=app2, POST=app3)
            d.add("/wilma/", _ANY_=app4)

        A request with any method to either ``/fred/`` or ``/wilma/``  will
        cause ``app`` or ``app4`` to called. A PUT to ``/barney/``
        will result in a 404, while a POST will call ``app3``.
        """
        appmap = self._appmap(args, kwargs)
        self.matchers.append(TemplatePredicate(path, appmap, self.ranges))

    def addregex(self, regex, *args, **kwargs):
        """Same exact operation as add, except that 'regex' is a regular
        expression and not a template. Named groups appead in the 
        positional args and named groups in the regular expression
        will appear in the named args.

        Example::
            def app(environ, start_response):
                start_response("200 Ok", [('Content-Type', "text/html")])
                return ["<h1>You requested: %s</h1>" % environ['wsgiorg.routing_args'][0][0] ] 

            d = Dispatcher()
            d.addregex("/([^/]+)/", app)

        """
        appmap = self._appmap(args, kwargs)
        self.matchers.append(RegexPredicate(regex, appmap, self.ranges))

