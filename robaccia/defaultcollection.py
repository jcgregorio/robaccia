"""
DefaultCollection

Takes the concept of WSGICollection and applies the 
following conventions:

1. If a member method returns None then it is interpreted as an empty dictionary
2. If a member method returns a dictionary then DefaultCollection will use
   the supplied renderer to produce a response from that dictionary.
3. There is a 'view' wsgiorg.routing_args that points to the sub-directory
   of "templates" that contains the templates.
4. If None, or a dictionary, are returned from a WSGI call then
   the renderer will be called, and will look up a template
   based on the view name and the member method name.  
5. For URI template matches that include an 'id', that 'id' will
   be passed in the dictionary to the renderer.

For example:

    from defaultcollection import Collection
    
    class RecipeCollection(DefaultCollection):
    
        # GET /cookbook/
        def list(environ, start_response):
            pass

    app = RecipeCollection('html', robaccia.render)

The list() member doesn't have a return value, so 
when a GET to "/cookbook/" is received, the template 
'cookbook/list.html' is rendered.

Renderer must implement:

   def render(environ, start_response, template_file, vars, headers={}, status="200 Ok", raw_etag=None)

See robaccia.render for a complete description.

"""



from wsgicollection import Collection
import os

class DefaultCollection(Collection):

    def __init__(self, ext, renderer):
        Collection.__init__(self)
        self._ext = ext
        self._renderer = renderer

    def __call__(self, environ, start_response):
        response = Collection.__call__(self, environ, start_response)
        if response == None:
            if self._id:
                response = {'id': self._id}
            else:
                response = {}
        if isinstance(response, dict):
            view = environ['wsgiorg.routing_args'][1].get('view', '.')
            template_file = os.path.join(view, self._function_name + "." + self._ext)
            return self._renderer(environ, start_response, template_file, response) 
        else:
            return response

