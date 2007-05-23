"""
WSGICollection

The idea of RESTful "Collections" has been percolating for years now.
A Collection is nothing more than a list, a container for resources.
While the APP_ defines a Collection in terms of Atom Feed and Entry documents
we don't have to be limited to that. It's time to complete a virtuous circle;
RESTLog_ inspired the Atom Publishing Protocol which 
inspired David Heinemeier Hansson's
`World of Resources`_ (pdf) and now it's time to come full circle and get that 
world of resources in Python.

In particular look at page 18 of that slide deck, where
dispatching to a collection of people, the following URIs
are to be handled:

+-------+-----------------+
| GET   |  /people        |
+-------+-----------------+
| POST  |  /people        |
+-------+-----------------+
| GET   |  /people/1      |
+-------+-----------------+
| PUT   |  /people/1      |
+-------+-----------------+
| DELETE|  /people/1      |
+-------+-----------------+
| GET   |  /people;new    |
+-------+-----------------+
| GET   |  /people/1;edit |
+-------+-----------------+


Now the 'new' and 'edit' URIs can be a bit ambiguous, only in the sense
that you might not guess right away that they are nouns, and remember,
URIs always identify nouns. I prefer to make the noun-ishness of them more apparent.

+-----+----------------------+
| GET |  /people;create_form |
+-----+----------------------+
| GET |  /people/1;edit_form |
+-----+----------------------+


In general, using the notation of wsgidispatcher_, we are looking at URIs 
of the form::

       /...people/[{id:word}][;{noun}] 

And dispatching requests to URIs of that form to functions with nice names::
        

  GET    /people               list()
  POST   /people               create()
  GET    /people/1             retrieve()
  PUT    /people/1             update()
  DELETE /people/1             delete()
  GET    /people;create_form   get_create_form()
  GET    /people/1;edit_form   get_edit_form()
  

WSGICollection relies on WSGI middleware before it in the call
chain to parse the URIs for {id} and {noun}, such 
as wsgidispatcher_. In theory it will 
work with any WSGI middleware that sets values for 'id' and 'noun' in 
environ['wsgiorg.routing_args'].
Here is how you would define a WSGI application that implements a collection::
    

    from wsgicollection import Collection
    
    class RecipeCollection(Collection):
    
        # GET /cookbook/
        def list(environ, start_response):
            pass
        # POST /cookbook/
        def create(environ, start_response):
            pass
    
        # GET /cookbook/1
        def retrieve(environ, start_response):
            pass
    
        # PUT /cookbook/1
        def update(environ, start_response):
            pass
    
        # DELETE /cookbook/1
        def delete(environ, start_response):
            pass
    
        # GET /cookbook/;create_form
        def get_create_form(environ, start_response):
            pass
    
        # POST /cookbook/1;comment_form
        def post_comment_form(environ, start_response):
            pass


And this class can be easily hooked up to wsgidispatcher::

    from wsgidispatcher import Dispacher 
    
    urls = Dispatcher()
    urls.add('/cookbook/[{id:word}][;{noun}]', RecipeCollection())

.. _RESTLog: http://bitworking.org/news/RESTLog_Overview    
.. _APP: http://bitworking.org/projects/atom/ 
.. _`World of Resources`: http://www.loudthinking.com/lt-files/worldofresources.pdf
.. _wsgidispatcher: wsgidispatcher.html
"""

import re
import cgi
from logging import info, error

COLL_MAP = {
    'GET': 'list',
    'POST': 'create'
    }

ENTRY_MAP = {
    'GET': 'retrieve',
    'PUT': 'update',
    'DELETE': 'delete'
}

class Collection(object):
    """
    """
    def __init__(self):
        self._id = "" 
        self._noun = ""
        self._function_name = ""

    def __call__(self, environ, start_response):
        self._id = "" 
        self._noun = ""
        self._function_name = ""
        if 'wsgiorg.routing_args' in environ:
            url_vars = environ['wsgiorg.routing_args'][1]
        elif 'selector.vars' in environ:
            url_vars = environ['selector.vars']
        else:
            start_response("500 Internal Server Error", [('content-type', 'text/plain')])
            #error("Environment variables for wsgicollection.Collection not provided via WSGI. %s" % str(environ))
            return ['Environment variables for wsgicollection.Collection not provided via WSGI.']

        self._id = url_vars.get('id', '')
        self._noun = url_vars.get('noun', '')
        method = environ['REQUEST_METHOD']
        if method == "POST" and environ.get('CONTENT_TYPE', '').find('x-www-form-urlencoded') > 0:
            size = int(environ.get('CONTENT_LENGTH', "-1"))
            environ['formpostdata'] = cgi.parse_qs(environ['wsgi.input'].read(size)) 
            if '_method' in environ['formpostdata'] and environ['formpostdata']['_method'][0] in ['PUT', 'DELETE']:
                method = environ['formpostdata']['_method'][0]
                info("wsgicollection: Rewrote request method to %s" % method)

        self._function_name = "%s_%s" % (method.lower(), self._noun)
        if not self._noun:
            method_map = self._id and ENTRY_MAP or COLL_MAP
            self._function_name = method_map.get(method, '') 

        if self._function_name and not self._function_name.startswith("_") and self._function_name in dir(self):
            return getattr(self, self._function_name)(environ, start_response)
        else:
            start_response("404 Not Found", [("Content-Type", "text/plain")])
            return ["Resource not found."]



