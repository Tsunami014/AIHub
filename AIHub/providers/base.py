import time
import random

__all__ = [
    'BaseProvider',
    'TestProvider'
]

class MetaAbc(type):
    def __str__(cls):
        return cls.NAME
    def __repr__(cls):
        return cls.REPR

class BaseProvider(metaclass=MetaAbc):
    NAME = 'Base Provider'
    REPR = '<BaseProvider>'
    @staticmethod
    def stream(model, conv):
        """
        # How to use

        ## Inputs
         - `model`: a list of strings which is the specified model.
         - `conv`: a list of dicts which is the conversation in the format `{'role': 'user OR bot', 'content': 'message'}`.

        ## Yield data in the format:

         - `yield " "+data` for sending data
         - `yield "!"+data` for sending done event and the completed message
        """
        yield "event: done\ndata: Hello, world!\n\n"
    
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
            message = conv[-2]['content']
        tot = ""
        for char in message:
            time.sleep(random.random()/2+0.5)
            tot += char
            yield " "+tot
        yield "!"+tot
    
    @staticmethod
    def getInfo(model):
        if model[0] == 'echo':
            if model[1] == 'all':
                return 'Test Provider\'s Echo provider provides a state-of-the-art echoing models, and the selected `all` model will echo all the conversation so far.'
            else:
                return 'Test Provider\'s Echo provider provides a state-of-the-art echoing models, and the selected `last` model will echo the user\'s last message.'
        return 'Test Provider\'s '+model[0]+' model will repeat it\'s phrase to the user.'
    
    @staticmethod
    def getHierachy():
        return ['Hello-world', 'Hello-AIHub', 'Testing', 'I-am-bot', 'No-idea', ['echo', ['all', 'last']]]
