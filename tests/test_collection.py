import re
from robaccia.wsgidispatcher import Dispatcher
from robaccia.wsgicollection import Collection
import unittest
from StringIO import StringIO

class TestDispatcher(unittest.TestCase):

    class MyColl(Collection):
        def __init__(self):
            self.called = {}

        def _ok(self, environ, start_response):
            start_response("200 Ok", [("Content-Type", "text/plain")])
            return ["Dispatched correctly."]

        def list(self, environ, start_response):
            self.called['list'] = True
            return self._ok(environ, start_response)

        def create(self, environ, start_response):
            self.called['create'] = True
            return self._ok(environ, start_response)
        
        def retrieve(self, environ, start_response):
            self.called['retrieve'] = True
            return self._ok(environ, start_response)
        
        def update(self, environ, start_response):
            self.called['update'] = True
            return self._ok(environ, start_response)
        
        def delete(self, environ, start_response):
            self.called['delete'] = True
            return self._ok(environ, start_response)

        def get_create_form(self, environ, start_response):
            self.called['get_create_form'] = True
            return self._ok(environ, start_response)

        def post_create_form(self, environ, start_response):
            self.called['post_create_form'] = True
            return self._ok(environ, start_response)

    def setUp(self):
        self.collection = self.MyColl() 
        self.select = Dispatcher()
        self.select.addregex("/blog/(?P<id>\w+)?(;(?P<noun>\w+))?", _ANY_=self.collection)
        
    def start_response(self, status, headers):
        self.status = int(status.split(' ')[0])

    def testretrieve(self):
        environ = {
            "PATH_INFO": "/blog/1",
            "REQUEST_METHOD": "GET"
        }
        self.select(environ, self.start_response)
        self.assertTrue(self.collection.called['retrieve'])

    def testupdate(self):
        environ = {
            "PATH_INFO": "/blog/1",
            "REQUEST_METHOD": "PUT"
        }
        self.select(environ, self.start_response)
        self.assertEqual(environ['wsgiorg.routing_args'][1]['id'], '1')
        self.assertTrue(self.collection.called['update'])

    def testdelete(self):
        environ = {
            "PATH_INFO": "/blog/1",
            "REQUEST_METHOD": "DELETE"
        }
        self.select(environ, self.start_response)
        self.assertTrue(self.collection.called['delete'])

    def testlist(self):
        environ = {
            "PATH_INFO": "/blog/",
            "REQUEST_METHOD": "GET"
        }
        self.select(environ, self.start_response)
        self.assertTrue(self.collection.called['list'])

    def testcreate(self):
        environ = {
            "PATH_INFO": "/blog/",
            "REQUEST_METHOD": "POST"
        }
        self.select(environ, self.start_response)
        self.assertTrue('create' in self.collection.called)

    def testcreate_form(self):
        environ = {
            "PATH_INFO": "/blog/;create_form",
            "REQUEST_METHOD": "GET"
        }
        self.select(environ, self.start_response)
        self.assertTrue('get_create_form' in self.collection.called)

    def testcreate_form_on_entry(self):
        environ = {
            "PATH_INFO": "/blog/1;create_form",
            "REQUEST_METHOD": "POST"
        }
        self.select(environ, self.start_response)
        self.assertTrue('post_create_form' in self.collection.called)
        self.assertEqual(200, self.status)

    def test_missing(self):
        environ = {
            "PATH_INFO": "/blog/1;no_create_form",
            "REQUEST_METHOD": "POST"
        }
        self.select(environ, self.start_response)
        self.assertFalse('no_create_form' in self.collection.called)
        self.assertEqual(404, self.status)

    def test_ok(self):
        environ = {
            "PATH_INFO": "/blog/1;_ok",
            "REQUEST_METHOD": "GET"
        }
        self.select(environ, self.start_response)
        self.assertFalse('_ok' in self.collection.called)
        self.assertEqual(404, self.status)


class TestDispatcherMisses(unittest.TestCase):
    class MyIncompleteColl(Collection):
        def __init__(self):
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

    def setUp(self):
        self.collection = self.MyIncompleteColl() 
        self.select = Dispatcher()
        self.select.addregex("/blog/(?P<id>\w+)?(;(?P<noun>\w+))?", _ANY_=self.collection)

    def start_response(self, status, headers):
        self.status = int(status.split(' ')[0])


    def test_missing(self):
        environ = {
            "PATH_INFO": "/blog/",
            "REQUEST_METHOD": "POST"
        }
        self.select(environ, self.start_response)
        self.assertEqual(404, self.status)

    def test_list(self):
        environ = {
            "PATH_INFO": "/blog/",
            "REQUEST_METHOD": "GET"
        }
        self.select(environ, self.start_response)
        self.assertTrue('list' in self.collection.called)
        self.assertEqual(200, self.status)

    def test_list_miss(self):
        environ = {
            "PATH_INFO": "/fredblog/",
            "REQUEST_METHOD": "GET"
        }
        self.select(environ, self.start_response)
        self.assertTrue(len(self.collection.called) == 0)
        self.assertEqual(404, self.status)

class TestUrlVars(unittest.TestCase):
    class MyColl(Collection):
        def __init__(self):
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
        
        def get_new_form(self, environ, start_response):
            self.called['get_new_form'] = True
            return self._ok(environ, start_response)


    def setUp(self):
        self.collection = self.MyColl() 

    def start_response(self, status, headers):
        self.status = int(status.split(' ')[0])

    def test_miss(self):
        environ = {
            "PATH_INFO": "/blog/",
            "REQUEST_METHOD": "POST",
            "wsgiorg.routing_args": ((), {})
        }
        self.collection(environ, self.start_response)
        self.assertEqual(404, self.status)

    def test_list(self):
        environ = {
            "PATH_INFO": "/blog/",
            "REQUEST_METHOD": "GET",
            "wsgiorg.routing_args": ((), {})
        }
        self.collection(environ, self.start_response)
        self.assertTrue('list' in self.collection.called)
        self.assertEqual(200, self.status)

    def test_delete(self):
        environ = {
            "PATH_INFO": "/blog/1",
            "REQUEST_METHOD": "DELETE",
            "wsgiorg.routing_args": ((), {'id': '1'})
        }
        self.collection(environ, self.start_response)
        self.assertTrue('delete' in self.collection.called) 
        self.assertEqual(200, self.status)

    def test_nouns(self):
        environ = {
            "PATH_INFO": "/blog/2;new_form",
            "REQUEST_METHOD": "GET",
            "wsgiorg.routing_args": ((), {'id': '2', 'noun': 'new_form'})
        }
        self.collection(environ, self.start_response)
        self.assertTrue('get_new_form' in self.collection.called) 
        self.assertEqual(200, self.status)

    def test_preconditions_fail(self):
        environ = {
            "PATH_INFO": "/blog/2;new_form",
            "REQUEST_METHOD": "GET",
        }
        self.collection(environ, self.start_response)
        self.assertEqual(500, self.status)

class TestFormEncoded(unittest.TestCase):
    class MyColl(Collection):
        def __init__(self):
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
        request_body = StringIO(urlencode(dict(_method="DELETE", data="some stuff")))
        environ = {
            "PATH_INFO": "/blog/",
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": "application/x-www-form-urlencoded",
            "wsgi.input": request_body,
            "wsgiorg.routing_args": ((), {'id': '1'})
        }
        self.collection(environ, self.start_response)
        self.assertEqual(200, self.status)
        self.assertTrue('delete' in self.collection.called)

    def test_form_url_encoded_content_length(self):
        from urllib import urlencode
        rep = urlencode(dict(_method="PUT", data="some stuff"))
        request_body = StringIO(rep)
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





