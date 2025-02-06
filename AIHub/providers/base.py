import time
import random

__all__ = [
    'BaseProvider',
    'TestProvider'
]

class MetaAbc(type):
    def __str__(cls):
        return cls.NAME

class BaseProvider(metaclass=MetaAbc):
    def stream(self, model, conv):
        """
        # How to use

        ## Yield data in the format:

         - `yield f"data: {data}\\n\\n"` for sending data
         - `yield f"event: done\\ndata: {data}\\n\\n"` for sending done event and the completed message
        """
        yield "event: done\ndata: Hello, world!\n\n"
    
    @staticmethod
    def getHierachy():
        return []
    
    NAME = 'Base Provider'
    def __str__(cls):
        return '<BaseProvider>'
    
    def __repr__(self):
        return str(self)

class TestProvider(BaseProvider):
    def stream(self, modeldat, conv):
        model = modeldat.split(':')
        if len(model) == 1:
            message = {
                'Hello-world': 'Hello, world!', 
                'Hello-AIHub': 'Hello, AIHub!', 
                'Testing': 'Testing...', 
                'I-am-bot!': 'I am bot! Who you are?', 
                'No-idea': 'I have no idea what I am doing!'
            }[model[0]]
        elif model[0] == 'echo':
            message = conv[-1]['message']
        tot = ""
        for char in message:
            time.sleep(random.random()*2+2)
            tot += char
            yield f"data: {tot}\n\n"
        yield f"event: done\ndata: {tot}\n\n"
    
    @staticmethod
    def getHierachy():
        return ['Hello-world', 'Hello-AIHub', 'Testing', 'I-am-bot', 'No-idea', ['echo', ['all', 'last']]]
    
    NAME = 'Test Provider'
    def __str__(cls):
        return '<TestProvider>'
