import unittest
from robaccia.wsgidispatcher import *

class Test(unittest.TestCase):
    def setUp(self):
        self.called = False
        self._404 = False 
        self.app_number = 0

    def _my404(self, environ, start_response):
        self._404 = True
        start_response("404 Missing", [])
        return []

    def _start_response(self, status, response_headers, exc_info=None):
        pass

    def _app(self, environ, start_response):
        start_response("200 Ok", [])
        self.called = True
        self.environ = environ.copy()

    def _app1(self, environ, start_response):
        self.app_number = 1
        return self._app(environ, start_response)

    def _app2(self, environ, start_response):
        self.app_number = 2
        return self._app(environ, start_response)

    def _app3(self, environ, start_response):
        self.app_number = 3
        return self._app(environ, start_response)

    def test_errors(self):
        d = Dispatcher()
        try:
            d.add("fred", 2, _ANY_="fred")
            self.fail("You can not specify both an application and a map of methods")
        except DuplicateArgumentError:
            pass

    def test_happy_path_no_method(self):
        d = Dispatcher()
        d.add("/fred/", self._app)
        d({'PATH_INFO': '/fred/', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertTrue(self.called)


    def test_happy_path(self):
        d = Dispatcher()
        d.add("/fred/", _ANY_ = self._app)
        d({'PATH_INFO': '/fred/', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertTrue(self.called)

    def test_happy_path_miss(self):
        d = Dispatcher()
        d.add("/fred/", _ANY_ = self._app)
        d({'PATH_INFO': '/fred', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self.called)

    def test_zero_length_path(self):
        d = Dispatcher()
        d.add("", _ANY_ = self._app)
        d({'PATH_INFO': '', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertTrue(self.called)

    def test_happy_path_method(self):
        d = Dispatcher()
        d.add("/fred/", GET = self._app)
        d({'PATH_INFO': '/fred/', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertTrue(self.called)

    def test_happy_path_method_miss(self):
        d = Dispatcher(self._my404)
        d.add("/fred/", PUT = self._app)
        d({'PATH_INFO': '/fred/', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self.called)
        self.assertTrue(self._404)

    def test_template_simple(self):
        d = Dispatcher()
        d.add("/{fred}/", GET = self._app)
        d({'PATH_INFO': '/barney/', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertTrue(self.called)
        self.assertFalse(self._404)
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['fred'], 'barney')

    def test_template_miss_method(self):
        d = Dispatcher(self._my404)
        d.add("/{fred}/", GET = self._app)
        d({'PATH_INFO': '/barney/', 'REQUEST_METHOD': 'PUT'}, self._start_response)
        self.assertFalse(self.called)
        self.assertTrue(self._404)

    def test_template_two_part(self):
        d = Dispatcher(self._my404)
        d.add("/{name}/[{name2}/]", GET = self._app)
        d({'PATH_INFO': '//', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self.called)
        d({'PATH_INFO': '/fred', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self.called)
        d({'PATH_INFO': '/fred/barney', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self.called)
        d({'PATH_INFO': '/fred/barney/', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertTrue(self.called)
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['name'], 'fred')
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['name2'], 'barney')

    def test_template_two_part_trailing(self):
        d = Dispatcher(self._my404)
        d.add("/{name}/[{name2}/]|", GET = self._app)
        d({'PATH_INFO': '//', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self.called)
        d({'PATH_INFO': '/fred', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self.called)
        d({'PATH_INFO': '/fred/barney', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertTrue(self.called)
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['name'], 'fred')
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['name2'], None)

    def test_template_new_char_range(self):
        d = Dispatcher(self._my404, {'real':'(\+|-)?[1-9]\.[0-9]*E(\+|-)?[0-9]+'})
        d.add("/{name:real}/", GET = self._app)
        d({'PATH_INFO': '/3.1415925535E-10/', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['name'], '3.1415925535E-10')

    def test_real_world_examples(self):
        urls = Dispatcher(self._my404)
        urls.add('/service/[{ctype:alpha}[/[{id:unreserved}/]]][;{noun}]', _ANY_=self._app1)
        urls.add('/comments/[{id:alnum}]',  _ANY_=self._app2)
        urls.add('/{alpha}/[{id}[/[{slug}]]]',  _ANY_=self._app3)

        urls({'PATH_INFO': '/service/;service_document', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self._404)
        self.assertEqual(1, self.app_number)
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['noun'], 'service_document')
        self.app_number = 0

        urls({'PATH_INFO': '/comments/2', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self._404)
        self.assertEqual(2, self.app_number)
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['id'], '2')
        self.app_number = 0

        urls({'PATH_INFO': '/draft/98/My-slug_name', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self._404)
        self.assertEqual(3, self.app_number)
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['slug'], 'My-slug_name')
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['id'], '98')

    def test_regex_happy_path(self):
        d = Dispatcher()
        d.addregex("/([^/]+)/", self._app)
        d({'PATH_INFO': '/fred/', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertTrue(self.called)
        self.assertEqual(self.environ['wsgiorg.routing_args'][0][0], 'fred')

    def test_regex_named(self):
        d = Dispatcher()
        d.addregex("/([^/]+)/(?P<fred>\d+)", self._app)
        d({'PATH_INFO': '/fred/123abc', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertTrue(self.called)
        self.assertEqual(self.environ['wsgiorg.routing_args'][0][0], 'fred')
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['fred'], '123')

    def test_extreme_laziness(self):
        """No rules, no method, and no path_info. We should
        not throw an exception"""
        d = Dispatcher()
        d({}, self._start_response)
        self.assertFalse(self.called)


    def test_semicolon(self):
        urls = Dispatcher(self._my404)
        urls.add('/service/[{id:word}][;{noun}]', _ANY_=self._app)

        urls({'PATH_INFO': '/service/fred;service_document', 'REQUEST_METHOD': 'GET'}, self._start_response)
        self.assertFalse(self._404)
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['noun'], 'service_document')
        self.assertEqual(self.environ['wsgiorg.routing_args'][1]['id'], 'fred')



class Template2Regex(unittest.TestCase):

    def test_template_failures(self):
        try:
            template2regex("[]]")
            self.fail("Should have thrown an exception")
        except InvalidTemplateError:
            pass
    
    def test_template_expand(self):
        cases = [
                ("{fred}", "^(?P<fred>[^/]+)$"),
                ("{fred:alpha}", "^(?P<fred>[a-zA-Z]+)$"),
                ("{fred:unreserved}", "^(?P<fred>[a-zA-Z\d\-\.\_\~]+)$"),
                ("{fred}|", "^(?P<fred>[^/]+)"),
                ("{fred}/{barney}|", "^(?P<fred>[^/]+)/(?P<barney>[^/]+)"),
                ("{fred}[/{barney}]|", "^(?P<fred>[^/]+)(/(?P<barney>[^/]+))?"),
                ("{fred}[/[{barney}]]|", "^(?P<fred>[^/]+)(/((?P<barney>[^/]+))?)?"),
                ("{fred}[/[{barney}]]", "^(?P<fred>[^/]+)(/((?P<barney>[^/]+))?)?$"),
                ("/{id}[/[{slug}]];edit_comment_form", "^/(?P<id>[^/]+)(/((?P<slug>[^/]+))?)?;edit_comment_form$"),
                ("/service/[{ctype:alpha}[/[{id}/]]][;{noun}]", "^/service/((?P<ctype>[a-zA-Z]+)(/((?P<id>[^/]+)/)?)?)?(;(?P<noun>[^/]+))?$"),
                ]
        for template, result in cases:
            self.assertEqual(template2regex(template), result)




