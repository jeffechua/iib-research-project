from flask import Flask
from .endpoints import query, bind, os

# Create the Flask app object
app = Flask(__name__)
app.debug = True
app.register_blueprint(query.blueprint, url_prefix='/query')
app.register_blueprint(bind.blueprint, url_prefix='/bind')
app.register_blueprint(os.blueprint, url_prefix='/os')

# Show an instructional message at the app root
@app.route('/')
def default():
    msg  = 'To see the result of an API call, enter a URL of the form:<BR>'
    msg += '&nbsp&nbsp [this_url]/api/v1/evaluate?val=[VAL]&order=[ORDER]<BR><BR>'
    msg += '&nbsp&nbsp (where [VAL] is a float and [ORDER] is an integer between 0 and 2)'
    msg += '&nbsp&nbsp [this_url] is the host and port currently shown in the address bar'
    return msg

