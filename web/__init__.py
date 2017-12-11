from flask import Flask
from flask_jsglue import JSGlue

app = Flask(__name__)
app.config.from_object('settings')

jsglue = JSGlue(app)

from home import views
from timechange import views
