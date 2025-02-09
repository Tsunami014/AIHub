import flask
from AIHub import providers
from AIHub.providers.base import format
from werkzeug.exceptions import BadRequest
from multiprocessing import Process, Queue
from threading import Lock
import json
import random
import requests
import sqlite3
import os

PATH = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(PATH, 'UI', 'template.html')) as f:
    TEMPLATE = f.read()

class DataBase:
    def __init__(self):
        if not os.path.exists(os.path.join(PATH, 'UI', 'databases')):
            os.mkdir(os.path.join(PATH, 'UI', 'databases'))
        self.lock = Lock()
        self.conn = sqlite3.connect(os.path.join(PATH, 'UI', 'databases', 'chats.db'), check_same_thread=False)
        self.execute('''CREATE TABLE IF NOT EXISTS chats (
  id INT,
  name VARCHAR(100),
  conv JSON
);''')
    
    def execute(self, sql, *params, returns=False):
        with self.lock:
            cur = self.conn.execute(sql, params)
            if returns:
                return cur.fetchall()
    
    def save(self):
        with self.lock:
            self.conn.commit()
    
    def __del__(self):
        self.process.kill()

DB = DataBase()

def apply(website):
    with open(os.path.join(PATH, 'UI', website)) as f:
        fc = f.read()
    return TEMPLATE.replace('<!-- INSERT CODE -->', fc)

app = flask.Flask(__name__)

@app.route('/')
def index():
    return apply('init.html')

@app.route('/proxy/google')
def google_proxy():
    q = flask.request.args.get('q')
    if not q:
        return flask.Response("Query parameter is missing.", status=400)
    url = f"https://www.google.com/search?q={q}&udm=2"
    resp = requests.get(url)
    return flask.Response(resp.text, status=resp.status_code, content_type='text/html')

def splitModel(model):
    spl = model.replace('\\', '/').split(':')
    allprovs = (getattr(providers, i) for i in providers.__all__ if i != 'BaseProvider')
    if spl == ['best']:
        return providers.TestProvider, ['best']
    elif spl == ['random']:
        return random.choice(list(allprovs)), ['random']
    provs = {str(i): i for i in allprovs}
    return provs[spl[0]], spl[1:]

Q = None
PRO = None

@app.route('/api/v1/ai/run/<modelStr>', methods=["POST"])
def aiRun(modelStr):
    global Q, PRO
    prov, model = splitModel(modelStr)

    Q = Queue()

    def runModel():
        out = ''
        try:
            data = flask.request.json
            for i in prov.stream(model, [{j: i[j] for j in i if j in ('role', 'content')} for i in data['conv']], data['opts']):
                out = i
                Q.put(i)
        except Exception as e:
            if out == '':
                outmod = model
            else:
                outmod = json.loads(out[:-1])['model']
            Q.put(out+format(f'Sorry, but an error has occured: {e}', outmod, True))
        Q.put(None)
    
    PRO = Process(target=runModel)
    PRO.start()
    
    def stream():
        global Q
        while True:
            out = Q.get()
            if out is None:
                return
            yield out

    return flask.Response(stream(), mimetype='text/event-stream')

@app.route('/api/v1/ai/stop', methods=["POST"])
def aiStop():
    global Q, PRO
    if PRO is None or Q is None:
        return flask.jsonify({"status": "error", "message": "AI process not running!"}), 400
    PRO.kill()
    Q.put(None)
    return flask.jsonify({"status": "success", "message": "AI process stopped."}), 200

@app.route('/api/v1/ai/get')
def getProvs():
    return flask.jsonify({'data': [[str(i), i.getHierachy()] for i in (getattr(providers, j) for j in providers.__all__ if j != 'BaseProvider')]}), 200

@app.route('/api/v1/ai/info/<modelStr>')
def info(modelStr):
    if modelStr == 'random':
        return flask.jsonify({'data': 'You have selected a RANDOM model!'}), 200
    prov, model = splitModel(modelStr)
    return flask.jsonify({'data': prov.getInfo(model)}), 200

@app.route('/api/v1/ai/opts/<modelStr>')
def opts(modelStr):
    if modelStr == 'random':
        return flask.jsonify({'opts': []}), 200
    prov, model = splitModel(modelStr)
    return flask.jsonify({'opts': prov.getOpts(model)}), 200

@app.route('/api/v1/chat', methods=['GET', 'POST'])
def newChat(method=None):
    meth = method or flask.request.method
    if meth == 'GET': # Get all chats
        return flask.jsonify({"status": "OK", "id": None, "data": DB.execute('SELECT * FROM chats', returns=True)}), 200
    elif meth == 'POST': # Create a new chat
        id = 1
        while DB.execute('SELECT * FROM chats WHERE id = ?', id, returns=True):
            id += 1
        try:
            data = flask.request.json
        except BadRequest:
            data = {}
        if 'name' not in data:
            data['name'] = 'Chat ' + str(id)
        if 'conv' not in data:
            data['conv'] = {'messages': []}
        else:
            data['conv'] = {'messages': data['conv']}
        DB.execute('INSERT INTO chats (id, name, conv) VALUES (?, ?, ?)', id, data['name'], json.dumps(data['conv']))
        DB.save()
        return flask.jsonify({"status": "OK", "id": id, "data": data}), 201
    else:
        return flask.jsonify({"status": "error", "id": None, "message": f"Method {meth} not allowed for id {id}"}), 405

@app.route('/api/v1/chat/<id>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_request(id, method=None):
    if not id.isnumeric():
        return flask.jsonify({"status": "error", "id": id, "message": "Invalid chat ID"}), 400
    meth = method or flask.request.method
    if meth == 'GET': # Get the chat
        chat = DB.execute('SELECT * FROM chats WHERE id = ?', id, returns=True)
        if chat:
            return flask.jsonify({"status": "OK", "id": id, "data": json.loads(chat[0][2])}), 200
        else:
            return flask.jsonify({"status": "error", "id": id, "message": "Chat not found"}), 404
    elif meth == 'POST': # Create a new chat
        try:
            data = flask.request.json
        except BadRequest:
            data = {}
        if 'name' not in data:
            data['name'] = 'Chat ' + id
        if 'conv' not in data:
            data['conv'] = {'messages': []}
        else:
            data['conv'] = {'messages': data['conv']}
        DB.execute('INSERT INTO chats (id, name, conv) VALUES (?, ?, ?)', id, data['name'], json.dumps(data['conv']))
        DB.save()
        return flask.jsonify({"status": "OK", "id": id, "data": data}), 201
    elif meth == 'PUT': # Update the chat
        try:
            data = flask.request.json
        except BadRequest:
            data = {} # So we can send back *our* error message, not it's
        if not data or ('name' not in data and 'conv' not in data):
            return flask.jsonify({"status": "error", "id": id, "message": "Invalid request data"}), 400
        if 'conv' in data:
            data['conv'] = json.dumps({'messages': data['conv']})
        chat = DB.execute('SELECT * FROM chats WHERE id = ?', id, returns=True)
        if chat:
            if 'name' not in data:
                DB.execute('UPDATE chats SET conv = ? WHERE id = ?', data['conv'], id)
            elif 'conv' not in data:
                DB.execute('UPDATE chats SET name = ? WHERE id = ?', data['name'], id)
            else:
                DB.execute('UPDATE chats SET name = ?, conv = ? WHERE id = ?', data['name'], data['conv'], id)
            DB.save()
            chat = DB.execute('SELECT * FROM chats WHERE id = ?', id, returns=True)
            return flask.jsonify({"status": "OK", "id": id, "data": json.loads(chat[0][2])}), 200
        else:
            return flask.jsonify({"status": "error", "id": id, "message": "Chat not found"}), 404
    elif meth == 'DELETE': # Delete the chat
        chat = DB.execute('SELECT * FROM chats WHERE id = ?', id, returns=True)
        if chat:
            DB.execute('DELETE FROM chats WHERE id = ?', id)
            DB.save()
            return flask.jsonify({"status": "OK", "id": id, "data": json.loads(chat[0][2])}), 200
        else:
            return flask.jsonify({"status": "error", "id": id, "message": "Chat not found"}), 404
    else:
        return flask.jsonify({"status": "error", "id": id, "message": f"Method {meth} not allowed for id {id}"}), 405

@app.route('/chat/<id>')
def chat(id):
    return apply('chat.html')

if __name__ == '__main__':
    app.run()
