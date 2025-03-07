import flask
from AIHub import providers
from AIHub.providers.base import format
from werkzeug.exceptions import BadRequest
from multiprocessing import Process, Queue
from threading import Lock
import re
import time
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

def apply(website, links=''):
    with open(os.path.join(PATH, 'UI', website)) as f:
        fc = f.read()
    return TEMPLATE.replace('<!-- INSERT CODE -->', fc).replace('<!-- Insert links -->', links)

app = flask.Flask(__name__)

PFPCache = {}
@app.route('/api/v1/ai/pfp/<model>')
def getPFP(model):
    if model in PFPCache:
        while PFPCache[model] is None:
            pass
        if PFPCache[model][0] + 60*5 < time.time():
            PFPCache.pop(model)
            return getPFP(model)
        return flask.jsonify({'status': 'OK', 'url': PFPCache[model][1]}), 200
    PFPCache[model] = None
    url = f"https://www.google.com/search?q={model.replace(' ', '+')}+AI+icon+-huggingface&udm=2&tbs=isz:i"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception as e:
        PFPCache[model] = (time.time(), None)
        return flask.jsonify({"status": "error", "message": str(e), "url": ""}), 400
    allImgs = re.findall('<img class="[^"]+" alt="" src="([^>]+)"/>', resp.text)
    img = allImgs[0]
    PFPCache[model] = (time.time(), img)
    return flask.jsonify({'status': 'OK', 'url': img}), 200

def splitModel(model):
    spl = model.replace('\\', '/').split(':')
    allprovs = (getattr(providers, i) for i in providers.__all__ if i != 'BaseProvider')
    if spl == ['best']:
        return providers.TestProvider, ['best']
    elif spl == ['random']:
        return random.choice(list(allprovs)), ['random']
    provs = {str(i): i for i in allprovs}
    return provs[spl[0]], spl[1:]

PROS = {}

class AIProc:
    def __init__(self, target, id, conv):
        if id in PROS:
            PROS[id].kill()
        self.id = id
        self.Q = Queue()
        self.conv = conv
        self.pro = Process(target=target, args=(self._handleIt,), daemon=True)
        self.pro.start()
        PROS[id] = self
    
    def __del__(self):
        if self.id in PROS:
            PROS.pop(self.id)
    
    def _handleIt(self, it):
        if it is not None:
            jsn = json.loads(f'[{it.rstrip(',')}]')
            DB.execute('UPDATE chats SET conv = ? WHERE id = ?', json.dumps({'messages': self.conv+[{'content': jsn[-1]['data'], 'role': 'bot', 'pfp': jsn[-1]['model']}]}), self.id)
            DB.save()
        else:
            self.__del__()
        self.Q.put(it)
    
    def streamF(self):
        while True:
            out = self.Q.get()
            if out is None:
                return
            yield out
    
    def kill(self):
        self.pro.kill()
        self.Q.put(None)
        # self.pro.join()
        self.__del__()
    
    def __bool__(self):
        return self.pro.is_alive()

@app.route('/api/v1/ai/start/<id>', methods=["POST"])
def aiRun(id):
    try:
        data = flask.request.json
        modelStr = data['modelStr']
        conv = data['conv']
        assert 'opts' in data
    except (BadRequest, KeyError, AssertionError):
        return flask.jsonify({"status": "error", "message": "Invalid request data!"}), 400
    prov, model = splitModel(modelStr)

    def runModel(Q):
        out = ''
        try:
            for i in prov.stream(model, [{j: i[j] for j in i if j in ('role', 'content')} for i in data['conv']], data['opts']):
                out = i
                Q(i)
        except Exception as e:
            if out == '':
                outmod = model
            else:
                outmod = json.loads(out[:-1])['model']
            Q(out+format(f'Sorry, but an error has occured: {e}', outmod, True))
        Q(None)
    
    AIProc(runModel, id, conv)
    return flask.jsonify({"status": "OK"}), 200

@app.route('/api/v1/ai/stream/<id>')
def aistream(id):
    if id not in PROS:
        return flask.jsonify({"status": "error", "message": "Stream ID does not exist or has been stopped!"}), 404
    return flask.Response(PROS[id].streamF(), mimetype='text/event-stream')

@app.route('/api/v1/ai/stop/<id>', methods=["POST"])
def aiStop(id):
    if id not in PROS:
        return flask.jsonify({"status": "error", "message": "Stream ID does not exist or has already been stopped!"}), 404
    PROS[id].kill()
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
            return flask.jsonify({"status": "OK", "id": id, "data": json.loads(chat[0][2]), "running": id in PROS}), 200
        else:
            return flask.jsonify({"status": "error", "id": id, "message": "Chat not found", "running": id in PROS}), 404
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

@app.route('/style.css')
def style():
    with open(os.path.join(PATH, 'UI', 'style.css')) as f:
        return f.read(), 200, {'Content-Type': 'text/css'}
@app.route('/chat/style.css')
def chatstyle():
    with open(os.path.join(PATH, 'UI', 'chat', 'extra.css')) as f:
        return f.read(), 200, {'Content-Type': 'text/css'}
@app.route('/script.js')
def script():
    with open(os.path.join(PATH, 'UI', 'script.js')) as f:
        return f.read(), 200, {'Content-Type': 'application/javascript'}
@app.route('/chat/script.js')
def chatscript():
    with open(os.path.join(PATH, 'UI', 'chat', 'extra.js')) as f:
        return f.read(), 200, {'Content-Type': 'application/javascript'}

@app.route('/')
def index():
    return apply('init.html')
@app.route('/chat/<id>')
def chat(id):
    return apply('chat/extra.html', '<link rel="stylesheet" href="/chat/style.css"><script src="/chat/script.js"></script>')

if __name__ == '__main__':
    app.run()
