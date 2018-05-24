from flask import Flask
from flask_scss import Scss

app = Flask(__name__)
app.secret_key = 'set_this_to_something_secret' #TODO
scss = Scss(app)
scss.update_scss()

import webapp.views