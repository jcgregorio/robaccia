import unittest
import robaccia
import os
import sys
from subprocess import Popen, PIPE
import shutil

SCRATCH = os.path.abspath(os.path.join("tests", "output"))
BASE = os.path.abspath(".")
FRED = """
def app(environ, start_response):
    start_response("200 Ok", [])
    id = environ['wsgiorg.routing_args'][1]['id']
    noun = environ['wsgiorg.routing_args'][1]['noun']
    return ["Hello %s-%s" % (id, noun)]
"""
class Test(unittest.TestCase):
    def _cleanup(self):
        if os.path.exists(SCRATCH):
            shutil.rmtree(SCRATCH)
        if not os.path.exists(SCRATCH):
            os.makedirs(SCRATCH)

    def _start_response(self, status, headers):
        pass

    def setUp(self):
        self._cleanup()
        self.cwd = os.getcwd()
        os.chdir(SCRATCH)

    def tearDown(self):
        self._cleanup()
        os.chdir(self.cwd)

    def test_deferred(self):
        output = Popen([os.path.join("..", "..", "bin", "robaccia-admin"), "createproject", "myprj"], stdout=PIPE).communicate()[0]
        os.chdir("myprj")

        f = file(os.path.join("views", "fred.py"), "w")
        f.write(FRED)
        f.close()

        sys.path.insert(0, os.getcwd()) 
        environ = {
                "wsgiorg.routing_args":
                (
                    [],
                    {
                        'view': 'fred',
                        'id': 'anid',
                        'noun': 'somenoun'
                    }
                )
           }
        self.assertEqual(["Hello anid-somenoun"], robaccia.deferred_collection(environ, self._start_response))

        os.chdir("..")


    def test_dispatcher(self):
        output = Popen([os.path.join("..", "..", "bin", "robaccia-admin"), "createproject", "myprj"], stdout=PIPE).communicate()[0]
        os.chdir("myprj")

        f = file(os.path.join("views", "fred.py"), "w")
        f.write(FRED)
        f.close()

        sys.path.insert(0, os.getcwd()) 
        import dispatcher
        environ = {
                "PATH_INFO": "/fred/someid;anoun",
                "REQUEST_METHOD": "GET",
                }
        self.assertEqual(["Hello someid-anoun"], dispatcher.app(environ, self._start_response))

        os.chdir("..")


    def test_render_template_paths(self):
        os.chdir(BASE)
        self.assertEqual(['{"a": 1}'], robaccia.render({}, self._start_response, 'list.json', {'a':1}))
        robaccia.TEMPLATE_DIRS = [os.path.join("tests", "input", "templates")]
        self.assertEqual(['<html><body><p>Hello World!</p></body></html>'], robaccia.render({}, self._start_response, 'list.html', {'a':1}, raw_etag="foo"))
        
    def test_parse_json(self):
        pass

