import os
import mimetypes
from google.appengine.ext.webapp import template

def render(start_response, template_file, template_values):
  contenttype, encoding = mimetypes.guess_type(template_file)
  if not contenttype:
    contenttype = "text/html"

  template_file = os.path.join(os.path.dirname(__file__), "templates", template_file)
  body = template.render(template_file, template_values)

  start_response("200 OK", [('Content-Type', contenttype)])
  return [body]

def webapprender(response, template_file, template_values):
  template_file = os.path.join(os.path.dirname(__file__), "index.html")
  response.out.write(template.render(template_file, template_values))

