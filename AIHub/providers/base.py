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


def format(info, model, done=False):
    return json.dumps({'data': str(info), 'done': done, 'model': model})+','

class BaseProvider(metaclass=MetaAbc):
    NAME = 'Base Provider'
    REPR = '<BaseProvider>'
    @staticmethod
    def stream(model, conv, opts):
        """
        # How to use

        ## Inputs
         - `model`: a list of strings which is the specified model.
         - `conv`: a list of dicts which is the conversation in the format `{'role': 'user OR bot', 'content': '...'}`.
         - `opts`: a dict of options which is the options provided by the user, in the form `{'id': value}`.

        ## How to yield data
         - `format(info, model, done=False)`
         - You *should* specify `done=True` (or just True, it's a positional or kw arg) for it to correctly finish the message
        """
        yield format('', model, True)
    
    @staticmethod
    def getInfo(model):
        return 'MODEL SELECTED: '+"'s ".join(model)
    
    @staticmethod
    def getOpts(model):
        return []
    
    @staticmethod
    def getHierachy():
        return []

class TestProvider(BaseProvider):
    NAME = 'Test Provider'
    REPR = '<TestProvider>'
    OPTS = {
        'best': 'Hello, world!', 
        'Hello-world': 'Hello, world!', 
        'Hello-AIHub': 'Hello, AIHub!', 
        'Testing': 'Testing...', 
        'I-am-bot!': 'I am bot! Who you are?', 
        'No-idea': 'I have no idea what I am doing!'
    }
    @staticmethod
    def stream(model, conv, opts):
        if len(model) == 1:
            if model[0] == 'random':
                message = random.choice(list(set(TestProvider.OPTS.values())))
            else:
                message = TestProvider.OPTS[model[0]]
        elif model[0] == 'echo':
            if model[1] == 'opts' or (model[1] == 'random' and random.choice([True, False])):
                message = str(opts)
            else:
                message = conv[-1]['content']
        tot = ""
        for char in message:
            time.sleep(max(random.random()/8, 0))
            tot += char
            yield format(tot, model)
        yield format(tot, model, True)
    
    @staticmethod
    def getOpts(model):
        if model == ['echo', 'opts']:
            return [
                {'type': 'header', 'label': 'HEADER'},
                {'id': 'NUM1', 'type': 'numInp', 'label': 'Hello this is a test', 'default': 0},
                {'id': 'BOOL1', 'type': 'boolInp', 'label': 'Test #2', 'default': True},
                {'id': 'CHOICE1', 'type': 'choiceInp', 'label': 'Make a choice!', 'default': 1, 'choices': ['Hello', 'Goodbye', 'Hello again', 'Another choice', 'Choice #5']}
            ]
        return []
    
    @staticmethod
    def getInfo(model):
        if model[0] == 'echo':
            t = 'Test Provider\'s Echo provider provides a state-of-the-art echoing models, and the selected '
            if model[1] == 'opts':
                return t+'`opts` model will echo the options provided!'
            else:
                return t+('`last`' if model[1] == 'last' else 'best (`last`)')+' model will echo the user\'s last message.'
        if model[0] == 'best':
            model = 'best (`Hello-world`)'
        else:
            model = f'`{model[0]}`'
        return 'Test Provider\'s '+model+' model will repeat it\'s phrase to the user.'
    
    @staticmethod
    def getHierachy():
        return ['Hello-world', 'Hello-AIHub', 'Testing', 'I-am-bot', 'No-idea', ['echo', ['opts', 'last']]]
