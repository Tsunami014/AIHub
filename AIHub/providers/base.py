import json
import time
import random

__all__ = [
    'BaseProvider',
    'TestProvider',
    'format'
]

class MetaAbc(type):
    def __str__(cls):
        return cls.NAME
    def __repr__(cls):
        return cls.REPR


def format(info, done=False):
    return json.dumps({'data': info, 'done': done})+','

class BaseProvider(metaclass=MetaAbc):
    NAME = 'Base Provider'
    REPR = '<BaseProvider>'
    @staticmethod
    def stream(model, conv):
        """
        # How to use

        ## Inputs
         - `model`: a list of strings which is the specified model.
         - `conv`: a list of dicts which is the conversation in the format `{'role': 'user OR bot', 'content': '...'}`.

        ## How to yield data
         - `format(info, done=False)`
         - You *should* specify `done=True` (or just True, it's a positional or kw arg) for it to correctly finish the message
        """
        yield format('', True)
    
    @staticmethod
    def getInfo(model):
        return 'MODEL SELECTED: '+"'s ".join(model)
    
    @staticmethod
    def getHierachy():
        return []

class TestProvider(BaseProvider):
    NAME = 'Test Provider'
    REPR = '<TestProvider>'
    @staticmethod
    def stream(model, conv):
        if len(model) == 1:
            message = {
                'Hello-world': 'Hello, world!', 
                'Hello-AIHub': 'Hello, AIHub!', 
                'Testing': 'Testing...', 
                'I-am-bot!': 'I am bot! Who you are?', 
                'No-idea': 'I have no idea what I am doing!'
            }[model[0]]
        elif model[0] == 'echo':
            if model[1] == 'last3':
                message = "\n".join([f'{i['role']}: {i['content']}' for i in conv[-3:]])
            else:
                message = conv[-1]['content']
        tot = ""
        for char in message:
            time.sleep(max(random.random()/8, 0))
            tot += char
            yield format(tot)
        yield format(tot, True)
    
    @staticmethod
    def getInfo(model):
        if model[0] == 'echo':
            t = 'Test Provider\'s Echo provider provides a state-of-the-art echoing models, and the selected '
            if model[1] == 'last3':
                return t+'`last3` model will echo the last 3 messages in the conversation so far.'
            else:
                return t+'`last` model will echo the user\'s last message.'
        return 'Test Provider\'s '+model[0]+' model will repeat it\'s phrase to the user.'
    
    @staticmethod
    def getHierachy():
        return ['Hello-world', 'Hello-AIHub', 'Testing', 'I-am-bot', 'No-idea', ['echo', ['last3', 'last']]]
