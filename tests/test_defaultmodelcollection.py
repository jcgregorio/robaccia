from robaccia.defaultmodelcollection import DefaultModelCollection
import robaccia
import unittest
import urllib
import StringIO

class MyColl(DefaultModelCollection):

    def list(self, environ, start_response):
        pass

    def create(self, environ, start_response):
        pass

    def retrieve(self, environ, start_response):
        pass

    def update(self, environ, start_response):
        pass

    def delete(self, environ, start_response):
        pass

from sqlalchemy import Table, Column, Integer, String, BoundMetaData

metadata = BoundMetaData('sqlite:///tests/output/database.db')
model = Table('fred', metadata,
        Column('id', Integer(), primary_key=True),
        Column('description', String(250))
        )


class Test(unittest.TestCase):

    def setUp(self):
        self.template_file = None 
        self.environ = None 
        self.vars = None 
        self.status = None
        self.repr = {}
        model.create(checkfirst=True) 

    def tearDown(self):
        model.drop(checkfirst=True) 


    def _renderer(self, environ, start_response, template_file, vars, headers={}, status="200 Ok", raw_etag=None):
        self.template_file = template_file
        self.environ = environ
        self.vars = vars
        start_response("200 Ok", headers.iteritems())

    def start_response(self, status, headers):
        self.status = int(status.split(' ')[0])

    def test_create(self):
        app = MyColl('html', self._renderer, robaccia.form_parser, model)
        body = urllib.urlencode({
                        "description": "First Post!"
                    })

        environ = {
            "REQUEST_METHOD": "POST",
            "wsgiorg.routing_args": ((), {
                'view': 'fred'
                }),
            "wsgi.input": StringIO.StringIO(body),
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
            "CONTENT_LENGTH": len(body),
        }
        app(environ, self.start_response)

        self.assertEqual(303, self.status)
        self.assertEqual(None, self.template_file)
        self.assertEqual(None, self.environ)

        environ = {
            "REQUEST_METHOD": "GET",
            "wsgiorg.routing_args": ((), {
                'id': '1',
                'view': 'fred'
                }),
        }
        app(environ, self.start_response)
        self.assertEqual(200, self.status)
        self.assertEqual('fred/retrieve.html', self.template_file)
        self.assertEqual(environ, self.environ)
        self.assertEqual(self.vars, {'primary': 'id', "row": {'id': 1, 'description': u'First Post!'}})

        body = urllib.urlencode({
                        "description": "Second Post!"
                    })
        environ = {
            "REQUEST_METHOD": "POST",
            "wsgiorg.routing_args": ((), {
                'view': 'fred'
                }),
            "wsgi.input": StringIO.StringIO(body),
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
            "CONTENT_LENGTH": len(body),
        }
        app(environ, self.start_response)

        environ = {
            "REQUEST_METHOD": "GET",
            "wsgiorg.routing_args": ((), {
                'view': 'fred'
                }),
        }
        app(environ, self.start_response)
        self.assertEqual(200, self.status)
        self.assertEqual('fred/list.html', self.template_file)
        self.assertEqual(environ, self.environ)
        self.assertEqual(len(self.vars['data']), 2)
 
        environ = {
            "REQUEST_METHOD": "DELETE",
            "wsgiorg.routing_args": ((), {
                'id': '1',
                'view': 'fred'
                }),
        }
        app(environ, self.start_response)
        self.assertEqual(303, self.status)
        
        environ = {
            "REQUEST_METHOD": "GET",
            "wsgiorg.routing_args": ((), {
                'view': 'fred'
                }),
        }
        app(environ, self.start_response)
        self.assertEqual(200, self.status)
        self.assertEqual('fred/list.html', self.template_file)
        self.assertEqual(environ, self.environ)
        self.assertEqual(len(self.vars['data']), 1)
 
        environ = {
            "REQUEST_METHOD": "GET",
            "wsgiorg.routing_args": ((), {
                'id': '1',
                'view': 'fred'
                }),
        }
        app(environ, self.start_response)
        self.assertEqual(404, self.status)
 
        environ = {
            "REQUEST_METHOD": "GET",
            "wsgiorg.routing_args": ((), {
                'id': '2',
                'view': 'fred'
                }),
        }
        app(environ, self.start_response)
        self.assertEqual(200, self.status)
        self.assertEqual('fred/retrieve.html', self.template_file)
        self.assertEqual(environ, self.environ)
        self.assertEqual(self.vars, {'primary': 'id', "row": {'id': 2, 'description': u'Second Post!'}})

class TestFormEncoded(unittest.TestCase):
    class MyColl(DefaultModelCollection):
        def __init__(self, ):
            DefaultModelCollection.__init__(self, 'html', robaccia.find_renderer('html'), robaccia.find_parser('html'), None)
            self.called = {}

        def _ok(self, environ, start_response):
            start_response("200 Ok", [("Content-Type", "text/plain")])
            return ["Dispatched correctly."]

        def list(self, environ, start_response):
            self.called['list'] = True
            return self._ok(environ, start_response)
        
        def delete(self, environ, start_response):
            self.called['delete'] = True
            return self._ok(environ, start_response)
        
        def update(self, environ, start_response):
            self.called['update'] = True
            return self._ok(environ, start_response)

        def get_new_form(self, environ, start_response):
            self.called['get_new_form'] = True
            return self._ok(environ, start_response)


    def setUp(self):
        self.collection = self.MyColl() 

    def start_response(self, status, headers):
        self.status = int(status.split(' ')[0])


    def test_form_url_encoded(self):
        from urllib import urlencode
        body = urlencode(dict(_method="DELETE", data="some stuff"))
        request_body = StringIO.StringIO(body)
        environ = {
            "PATH_INFO": "/blog/",
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
            "CONTENT_LENGTH": len(body),
            "wsgi.input": request_body,
            "wsgiorg.routing_args": ((), {'id': '1'})
        }
        self.collection(environ, self.start_response)
        self.assertEqual(200, self.status)
        self.assertTrue('delete' in self.collection.called)

    def test_form_url_encoded_content_length(self):
        from urllib import urlencode
        rep = urlencode(dict(_method="PUT", data="some stuff"))
        request_body = StringIO.StringIO(rep)
        environ = {
            "PATH_INFO": "/blog/",
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
            "CONTENT_LENGTH": str(len(rep)),
            "wsgi.input": request_body,
            "wsgiorg.routing_args": ((), {'id': '1'})
        }
        self.collection(environ, self.start_response)
        self.assertEqual(200, self.status)
        self.assertTrue('update' in self.collection.called)





