import ollama
import random
from AIHub.providers.base import BaseProvider, format

def findUnit(x):
    thresholds = [
        (1024**3, 'GB'),
        (1024**2, 'MB'),
        (1024**1, 'KB')
    ]
    for threshold, unit in thresholds:
        if x >= threshold:
            return f"{round(x / threshold, 2)} {unit}"
    # If not found, convert to bytes
    return f"{x} B"

class OllamaProvider(BaseProvider):
    NAME = 'Ollama Provider'
    REPR = '<OllamaProvider>'
    @staticmethod
    def stream(model, conv, opts):
        ms = ollama.list().models
        if model == ['best']:
            realm = sorted(ms, key=lambda x: x.size)[-1]
            model = realm.model
        elif model == ['random']:
            realm = random.choice(ms)
            model = realm.model
        else:
            model = model[0].replace(';', ':')
            realm = [i for i in ms if i.model == model][0]
        end = ""
        yield format('', [realm.details.parent_model or 'OLLAMA', model])
        for part in ollama.chat(model, [ollama.Message(role=i['role'].replace('bot', 'assistant'), content=i['content']) for i in conv], stream=True):
            end += part.message.content
            yield format(end, [realm.details.parent_model or 'OLLAMA', model], part.done)
    
    @staticmethod
    def getInfo(model):
        pref = ""
        ms = ollama.list().models
        if model == ['best']:
            model = sorted(ms, key=lambda x: x.size)[-1]
            pref = f'Ollama\'s BEST model will be the one requiring the highest computational value: {model.model}.\n'
        elif model == ['random']:
            return 'Ollama\'s random model will randomly choose a model!'
        else:
            model = model[0].replace(';', ':')
            model = [i for i in ms if i.model == model][0]
        deets = model.details
        time = model.modified_at
        return f"""{pref}{model.model} is a {deets.format} model{" whose parent is "+deets.parent_model if deets.parent_model else ""} and is in the \
{deets.family} family.
It is {deets.parameter_size}, with a quantization level of {deets.quantization_level} and a size of ~{findUnit(model.size)}.
It was last modified at {time.day}/{time.month}/{time.year}, at {time.hour}:{time.minute}:{time.second}."""
    
    @staticmethod
    def getHierachy():
        ms = ollama.list().models
        return [i.model.replace(':', ';') for i in ms]
        # outs = {}
        # for i in ms:
        #     spl = i.model.split(':')
        #     if spl[0] in outs:
        #         outs[spl[0]].append(spl[1])
        #     else:
        #         outs[spl[0]] = [spl[1]]
        # return [[i, j] for i, j in outs.items()]
