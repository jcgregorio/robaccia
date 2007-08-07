import unittest
import os
from subprocess import Popen, PIPE
import shutil
import sys

sys.path.insert(0, os.getcwd())

SCRATCH = os.path.abspath(os.path.join("tests", "output"))

class Test(unittest.TestCase):
    def _cleanup(self):
        if os.path.exists(SCRATCH):
            shutil.rmtree(SCRATCH)
        if not os.path.exists(SCRATCH):
            os.makedirs(SCRATCH)

    def setUp(self):
        self._cleanup()
        self.cwd = os.getcwd()
        os.chdir(SCRATCH)

    def tearDown(self):
        self._cleanup()
        os.chdir(self.cwd)

    def test_create_project(self):
        output = Popen([os.path.join("..", "..", "bin", "robaccia-admin"), "createproject", "myprj"], stdout=PIPE).communicate()[0]
        self.assertTrue(os.path.isdir(os.path.join("myprj", "views")))
        self.assertTrue(os.path.exists(os.path.join("myprj", "views", "__init__.py")))
        self.assertTrue(os.path.exists(os.path.join("myprj", "models", "__init__.py")))
        self.assertTrue(os.path.exists(os.path.join("myprj", "tests", "__init__.py")))
        self.assertTrue(os.path.exists(os.path.join("myprj", "models")))
        self.assertTrue(os.path.exists(os.path.join("myprj", "tests")))
        self.assertTrue(os.path.exists(os.path.join("myprj", "templates")))
        self.assertTrue(os.path.exists(os.path.join("myprj", "dispatcher.py")))

    def test_add_views(self):
        output = Popen([os.path.join("..", "..", "bin", "robaccia-admin"), "createproject", "myprj"], stdout=PIPE).communicate()[0]
        os.chdir("myprj")
        output = Popen([os.path.join("..", "..", "..", "bin", "robaccia-admin"), "addview", "fred", "--type=html"], stdout=PIPE).communicate()[0]
        self.assertTrue(os.path.isdir("views"))
        self.assertTrue(os.path.exists(os.path.join("views", "fred.py")))
        self.assertTrue(os.path.exists(os.path.join("templates", "fred", "list.html")))
        self.assertTrue(os.path.exists(os.path.join("templates", "fred", "retrieve.html")))

        output = Popen([os.path.join("..", "..", "..", "bin", "robaccia-admin"), "addmodelview", "barney", "--type=html"], stdout=PIPE).communicate()[0]
        self.assertTrue(os.path.isdir("models"))
        self.assertTrue(os.path.exists(os.path.join("views", "barney.py")))
        self.assertTrue(os.path.exists(os.path.join("models", "barney.py")))
        self.assertTrue(os.path.exists(os.path.join("templates", "barney", "retrieve.html")))


