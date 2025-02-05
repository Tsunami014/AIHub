import time
import random

__all__ = [
    'BaseProvider',
    'TestProvider'
]

class BaseProvider:
    def stream(self, model, conv):
        """
        # How to use

        ## Yield data in the format:

         - `yield f"data: {data}\\n\\n"` for sending data
         - `yield f"event: done\\ndata: {data}\\n\\n"` for sending done event and the completed message
        """
        yield "event: done\ndata: Hello, world!\n\n"
    
    def getModels(self):
        return []
    
    def __str__(self):
        """Also is used for the provider's name"""
        return 'BaseProvider'

class TestProvider(BaseProvider):
    def stream(self, model, conv):
        message = {
            'Hello-world': 'Hello, world!', 
            'Hello-AIHub': 'Hello, AIHub!', 
            'Testing': 'Testing...', 
            'I-am-bot!': 'I am bot! Who you are?', 
            'No-idea': 'I have no idea what I am doing!'
        }[model]
        tot = ""
        for char in message:
            time.sleep(random.random()*2+2)
            tot += char
            yield f"data: {tot}\n\n"
        yield f"event: done\ndata: {tot}\n\n"
    
    def getModels(self):
        return ['Hello-world', 'Hello-AIHub', 'Testing', 'I-am-bot', 'No-idea']
    
    def __str__(self):
        return 'TestProvider'
