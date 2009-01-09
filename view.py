import robaccia
import model
import cgi
import logging

from wsgiutility import wsgirouting

def index(environ, start_response):
  entries = model.BlogEntry.all().order("-created").fetch(20)
  return robaccia.render(start_response, 'index.html', locals())

def member_get(environ, start_response):
  id = int(environ['wsgiorg.routing_args'][1]['id'])
  entry = model.BlogEntry.get_by_id(int(id))
  return robaccia.render(start_response, 'entry.html', locals())

def create(environ, start_response):
  req = dict(cgi.parse_qsl(environ['wsgi.input'].read()))
  model.BlogEntry(title=req['title'], content=req['content']).put()
  start_response("303 See Other", [('Location', '/blog/')])
  return []
   
@wsgirouting
def member_edit_form(environ, start_response, id):
  entry = model.BlogEntry.get_by_id(int(id))
  return robaccia.render(start_response, 'entry_form.html', locals())
    
def member_update(environ, start_response):
  id = int(environ['wsgiorg.routing_args'][1]['id'])
  entry = model.BlogEntry.get_by_id(id)
  req = dict(cgi.parse_qsl(environ['wsgi.input'].read()))
  entry.title = req['title']
  entry.content = req['content']
  entry.put()
  start_response("303 See Other", [('Location', '/blog/' + str(id) + "/edit_form")])
  return []
  

