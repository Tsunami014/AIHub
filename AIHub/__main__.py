import flask
import os

PATH = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(PATH, 'UI', 'template.html')) as f:
    TEMPLATE = f.read()

def apply(website):
    with open(os.path.join(PATH, 'UI', website)) as f:
        fc = f.read()
    return TEMPLATE.replace('<!-- INSERT CODE -->', fc)

app = flask.Flask(__name__)

@app.route('/')
def index():
    return apply('init.html')

@app.route('/chat/<id>')
def chat(id):
    return apply('chat.html')

if __name__ == '__main__':
    app.run()
