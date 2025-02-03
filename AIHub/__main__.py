import flask
import os

PATH = os.path.dirname(os.path.abspath(__file__))

app = flask.Flask(__name__)

@app.route('/')
def index():
    return open(os.path.join(PATH, 'UI', 'index.html')).read()

if __name__ == '__main__':
    app.run()
