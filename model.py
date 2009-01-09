from google.appengine.ext import db

class BlogEntry(db.Model):
  title = db.StringProperty()
  content = db.TextProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now_add=True)
  
    

