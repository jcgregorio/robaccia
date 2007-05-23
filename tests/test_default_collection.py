from robaccia.defaultcollection import DefaultCollection
import unittest

class MyColl(DefaultCollection):

    def list(self, environ, start_response):
        pass

    def retrieve(self, environ, start_response):
        pass

    def update(self, environ, start_response):
        start_response("300 Multiple Choices", [('location', 'http://example.org')])
        return ['Look over there.']


class Test(unittest.TestCase):

    def setUp(self):
        self.template_file = None 
        self.environ = None 
        self.vars = None 
        self.status = None

    def _renderer(self, environ, start_response, template_file, vars, headers={}, status="200 Ok", raw_etag=None):
        self.template_file = template_file
        self.environ = environ
        self.vars = vars
        start_response("200 Ok", headers.iteritems())

    def start_response(self, status, headers):
        self.status = int(status.split(' ')[0])

    def test_none(self):
        app = MyColl('html', self._renderer)
        environ = {
            "REQUEST_METHOD": "GET",
            "wsgiorg.routing_args": ((), {
                'view': 'fred'
                })
        }
        app(environ, self.start_response)
        self.assertEqual(200, self.status)
        self.assertEqual('fred/list.html', self.template_file)
        self.assertEqual(environ, self.environ)


    def test_none_retrieve(self):
        app = MyColl('json', self._renderer)
        environ = {
            "REQUEST_METHOD": "GET",
            "wsgiorg.routing_args": ((), {
                'id': '1',
                'view': 'barney'
                })
        }
        app(environ, self.start_response)
        self.assertEqual(200, self.status)
        self.assertEqual('barney/retrieve.json', self.template_file)
        self.assertEqual(environ, self.environ)
        self.assertEqual(self.vars, {'id': '1'})


    def test_update(self):
        "The default render behavior can be over-ridden"
        app = MyColl('html', self._renderer)
        environ = {
            "REQUEST_METHOD": "PUT",
            "wsgiorg.routing_args": ((), {
                'id': '1',
                'view': 'fred'
                })
        }
        app(environ, self.start_response)
        self.assertEqual(300, self.status)
        self.assertEqual(None, self.template_file)
        self.assertEqual(None, self.environ)
        self.assertEqual(None, self.vars)







