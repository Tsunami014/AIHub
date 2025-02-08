import g4f.Provider
from g4f.client import Client
from AIHub.providers.base import BaseProvider, format
import random

__all__ = ['G4FProvider']

def getL(prov):
    if not prov.working or prov.url is None:
        return [None, None]
    try:
        models = prov.models
    except AttributeError:
        try:
            models = prov.get_models()
        except AttributeError:
            models = []
    name = prov.__name__
    prefix = ('🔒' if prov.needs_auth else '🔐')
    return [prefix+name, models]

class G4FProvider(BaseProvider):
    NAME = 'GPT4Free Provider'
    REPR = '<G4FProvider>'
    @staticmethod
    def stream(model, conv):
        out = ''
        if model == ['best']:
            for prov in g4f.Provider.__providers__:
                if prov.needs_auth or not prov.supports_stream:
                    continue
                li = getL(prov)
                if li[1]:
                    model = [li[0], 'best']
                    break
            else:
                yield format('', model)
                yield format('Sorry, but an error has occured: No provider found!', model, True)
                return
        elif model == ['random']:
            hierachy = G4FProvider.getHierachy()
            model = random.choice(hierachy)
            model = [model[0], random.choice(model[1])]
        prov = g4f.Provider.__map__[model[0][1:]]
        if model[1] == 'random':
            try:
                avmodels = prov.models
            except AttributeError:
                avmodels = prov.get_models()
            model = [model[0], random.choice(avmodels)]
        elif model[1] == 'best':
            model = [model[0], prov.default_model]
        try:
            strem = prov.supports_stream
            resp = Client().chat.completions.create(
                model=model[-1],
                stream=strem,
                provider=prov,
                messages=conv,
                # web_search=False,
            )
            if strem:
                for i in resp:
                    resp = i.choices[0].delta.content
                    if resp:
                        out += resp
                    yield format(out, model)
                yield format(out, model, True)
            else:
                yield format(resp.choices[0].delta.content, model)
                yield format(resp.choices[0].delta.content, model, True)
        except Exception as e:
            yield format(out, model)
            yield format(f'{out}{"\n" if out != "" else ""}Sorry, but an error has occured: {e}', model, True)
    
    @staticmethod
    def getInfo(model):
        firstBest = False
        if model == ['random']:
            return 'You have selected a RANDOM model from GPT4Free!'
        elif model == ['best']:
            firstBest = True
            for prov in g4f.Provider.__providers__:
                if prov.needs_auth or not prov.supports_stream:
                    continue
                li = getL(prov)
                if li[1]:
                    model = [li[0], 'best']
                    break
            else:
                return 'Sorry, but an error has occured: No provider found!'
        prov = g4f.Provider.__map__[model[0][1:]]
        secBest = model[1] == 'best'
        if secBest:
            model = [model[0], prov.default_model]
        return f"""{model[0][1:]}'s {"best " if secBest else ""}model {model[-1]} is {"GPT4Free's best" if firstBest else "a GPT4Free"} model, which has the following properties:
 - {'Does not require' if not prov.needs_auth else 'Requires'} authentification
 - {'Supports' if prov.supports_stream else 'Does not support'} streaming
 - located at {prov.url}"""
    
    @staticmethod
    def getHierachy():
        out = [getL(prov) for prov in g4f.Provider.__providers__]
        return [i for i in out if i[1]]
