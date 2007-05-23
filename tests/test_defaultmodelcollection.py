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
        environ = {
            "REQUEST_METHOD": "POST",
            "wsgiorg.routing_args": ((), {
                'view': 'fred'
                }),
            "wsgi.input": StringIO.StringIO(
                urllib.urlencode({
                        "description": "First Post!"
                    })
                )
        }
        app(environ, self.start_response)

        self.assertEqual(200, self.status)
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

        environ = {
            "REQUEST_METHOD": "POST",
            "wsgiorg.routing_args": ((), {
                'view': 'fred'
                }),
            "wsgi.input": StringIO.StringIO(
                urllib.urlencode({
                        "description": "Second Post!"
                    })
                )
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
        self.assertEqual(200, self.status)
        
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


