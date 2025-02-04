import json
from werkzeug.exceptions import BadRequest
import flask
import sqlite3
import os

PATH = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(PATH, 'UI', 'template.html')) as f:
    TEMPLATE = f.read()

class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect(os.path.join(PATH, 'UI', 'databases', 'chats.db'), check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.execute('''CREATE TABLE IF NOT EXISTS chats (
  id INT,
  name VARCHAR(100),
  conv JSON
);''')
    
    def execute(self, sql, *params):
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()
    
    def save(self):
        self.conn.commit()
    
    def __del__(self):
        self.conn.close()

DB = DataBase()

def apply(website):
    with open(os.path.join(PATH, 'UI', website)) as f:
        fc = f.read()
    return TEMPLATE.replace('<!-- INSERT CODE -->', fc)

app = flask.Flask(__name__)

@app.route('/')
def index():
    return apply('init.html')

@app.route('/api/v1/chat', methods=['POST'])
def newChat(method=None):
    meth = method or flask.request.method
    if meth == 'POST': # Create a new chat
        id = 1
        while DB.execute('SELECT * FROM chats WHERE id = ?', id):
            id += 1
        try:
            data = flask.request.json
        except BadRequest:
            data = {}
        if 'name' not in data:
            data['name'] = 'Chat ' + str(id)
        if 'conv' not in data:
            data['conv'] = {'messages': []}
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
        chat = DB.execute('SELECT * FROM chats WHERE id = ?', id)
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
        DB.execute('INSERT INTO chats (id, name, conv) VALUES (?, ?, ?)', id, data['name'], data['conv'])
        DB.save()
        return flask.jsonify({"status": "OK", "id": id, "data": data}), 201
    elif meth == 'PUT': # Update the chat
        try:
            data = flask.request.json
        except BadRequest:
            data = {} # So we can send back *our* error message, not it's
        if not data or ('name' not in data and 'conv' not in data):
            return flask.jsonify({"status": "error", "id": id, "message": "Invalid request data"}), 400
        chat = DB.query('SELECT * FROM chats WHERE id = ?', id)
        if chat:
            if 'name' not in data:
                DB.execute('UPDATE chats SET name = ? WHERE id = ?', data['conv'], id)
            elif 'conv' not in data:
                DB.execute('UPDATE chats SET conv = ? WHERE id = ?', data['name'], id)
            else:
                DB.execute('UPDATE chats SET name = ?, conv = ? WHERE id = ?', data['name'], data['conv'], id)
            DB.save()
            chat = DB.execute('SELECT * FROM chats WHERE id = ?', id)
            return flask.jsonify({"status": "OK", "id": id, "data": json.loads(chat[0][2])}), 200
        else:
            return flask.jsonify({"status": "error", "id": id, "message": "Chat not found"}), 404
    elif meth == 'DELETE': # Delete the chat
        chat = DB.query('SELECT * FROM chats WHERE id = ?', id)
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
