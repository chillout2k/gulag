import requests,json,sys

class GulagClientException(Exception):
  message = None
  def __init__(self,message):
    self.message = message

class GulagClient:
  api_uri = None
  api_key = None
  headers = None

  def __init__(self,args):
    self.api_uri = args['api_uri']
    self.api_key = args['api_key']
    self.headers = {
      'Content-Type': 'application/json',
      'API_KEY': self.api_key
    }

  def whoami(self):
    return type(self).__name__ + "::" + sys._getframe(1).f_code.co_name + "(): "

  def handle_response(self,response):
    if response.status_code == 200:
      return json.loads(response.content.decode('utf-8'))
    elif response.status_code == 400 or response.status_code == 500:
      error = json.loads(response.content.decode('utf-8'))
      raise GulagClientException(self.whoami() + error['message'])

  def get_quarmails(self,args):
    if 'filters' in args:
      try:
        # jqgrid-style filters must be JSON-encoded
        args['filters'] = json.dumps(args['filters'])
      except TypeError as e:
        raise GulagClientException(e.__str__)
    try:
      response = requests.get(
        self.api_uri + '/api/v1/quarmails',
        headers=self.headers,
        params=args
      )
    except Exception as e:
      raise GulagClientException(self.whoami() + str(e)) from e
    try:
      return self.handle_response(response)
    except GulagClientException as e:
      raise GulagClientException(self.whoami() + e.message) from e
