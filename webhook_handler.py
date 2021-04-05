from flask import Flask
from flask import request

print(Flask)

import bot
import gl


app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        process_request(request)
        return '<h2>Bot is currently running...</h2>'
    return '<h2><h2>Bot is currently running...</h2></h2>'

def process_request(request):
    pass