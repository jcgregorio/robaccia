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
"cookbook/list.html" is rendered.

Renderer must implement:

   def render(environ, start_response, template_file, vars, headers={}, status="200 Ok", raw_etag=None)

See robaccia.render for a complete description.

"""



from wsgicollection import Collection
import os
from robaccia import http200, http405, http404, http303

class DefaultModelCollection(Collection):

    def __init__(self, ext, renderer, parser, model):
        Collection.__init__(self)
        self._ext = ext
        self._renderer = renderer # converts dicts to representations
        self._model = model
        self._parser = parser     # converts representations to dicts
        self._repr = {}           # request representation as a dict()

    def __call__(self, environ, start_response):

        size = environ.get('CONTENT_LENGTH', '')
        if size and self._parser:
            size = int(size)
            self._repr = self._parser(environ['wsgi.input'].read(size)) 
            if environ['REQUEST_METHOD'] == "POST" and '_method' in self._repr and self._repr['_method'] in ['PUT', 'DELETE']:
                environ['REQUEST_METHOD'] = self._repr['_method']

        response = Collection.__call__(self, environ, start_response)

        if response == None:
            primary = self._model.primary_key.columns.keys()[0]
            view = environ['wsgiorg.routing_args'][1].get('view', '.')
            template_file = os.path.join(view, self._function_name + "." + self._ext)
            method = environ.get('REQUEST_METHOD', 'GET')
            if self._id:
                if method == "POST" and "_method" in self._repr and self._repr["_method"] in ["PUT", "DELETE"]:
                    method = self._repr["_method"]
                    del self._repr["_method"]
                if method == 'GET':
                    result = self._model.select(self._model.c[primary]==self._id).execute()
                    row = result.fetchone()
                    if None == row:
                        return http404(environ, start_response)
                    data = dict(zip(result.keys, row))
                    return self._renderer(environ, start_response, template_file, {"row": data, "primary": primary}) 
                elif method == 'PUT':
                    self._model.update(self._model.c[primary]==self._id).execute(self._repr)
                    return http303(environ, start_response, self._id)
                elif method == 'DELETE':
                    self._model.delete(self._model.c[primary]==self._id).execute()
                    return http303(environ, start_response, "./")
                else:
                    print method
                    return http405(environ, start_response)
            else:
                if method == 'GET':
                    result = self._model.select().execute()
                    meta = self._model.columns.keys()
                    data = [dict(zip(result.keys, row)) for row in result.fetchall()]
                    return self._renderer(environ, start_response, template_file, {"data": data, "primary": primary, "meta": meta}) 
                elif method == 'POST':
                    results = self._model.insert(self._repr).execute()
                    return http303(environ, start_response, str(results.last_inserted_ids()[0]))
        else:
            return response

