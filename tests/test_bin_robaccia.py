import unittest
import os
from subprocess import Popen, PIPE
import shutil

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

