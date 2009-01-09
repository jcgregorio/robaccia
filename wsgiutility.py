
def wsgirouting(f):
  """
  Decorator to turn WGSI call into a call the contains
  environ and start_response then all of 
  the 'wsgiorg.routing_args' as *args and **kwargs.
  """
  def wrapper(environ, start_response):
    args, kwargs = environ['wsgiorg.routing_args']
    return f(environ, start_response, *args, **kwargs)
  return wrapper

