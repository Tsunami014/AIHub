import g4f.Provider
from g4f.client import Client
from AIHub.providers.base import BaseProvider, format
import random
import time

__all__ = ['G4FProvider']

PREFIX_LEN = 2

def timeCache(func, wait=0): # 60*2 = 2 mins
    cache = {}
    def func2(*args):
        match = args
        if match in cache:
            created, out = cache[match]
            if time.time() < created + wait:
                return out
        new = func(*args)
        cache[match] = (time.time(), new)
        return new
    
    return func2

def getMPrefxs(prov, model):
    img = "💬"
    if hasattr(prov, 'image_models'):
        if model in prov.image_models:
            img = "🖼️"
    if hasattr(prov, 'vision_models'):
        if model in prov.vision_models:
            img += "👀"
    return img

def getProvModels(prov):
    try:
        models = prov.models
    except AttributeError:
        try:
            models = prov.get_models()
        except AttributeError:
            models = []
    aliases = getattr(prov, 'model_aliases', {}).copy()
    aliases.update(getattr(prov, 'models_aliases', {}))
    return models + [m for m in aliases.values() if m not in models]

@timeCache
def getModelMap(prov):
    aliases = getattr(prov, 'model_aliases', {}).copy()
    aliases.update(getattr(prov, 'models_aliases', {}))
    aliasesRev = {j: i for i, j in aliases.items()}
    return {getMPrefxs(prov, i)+' '+(aliasesRev[i] if i in aliasesRev else i): i for i in getProvModels(prov)}

def getProvPrefix(prov):
    models = getProvModels(prov)
    name = getattr(prov, 'label', prov.__name__)
    prefix = ('🔒' if prov.needs_auth else '🔐')+("💬" if (not hasattr(prov, "image_models")) or any(i not in prov.image_models for i in models) else "")+("🖼️" if bool(getattr(prov, "image_models", False)) else "")+("👀" if bool(getattr(prov, "vision_models", False)) else "")
    return prefix+' '+name

@timeCache
def getProvMap():
    return {getProvPrefix(i): i for i in g4f.Provider.__providers__ if i.working}


def convertModel(prov, model):
    if model in ('best', 'random'):
        return model
    prov = g4f.Provider.__map__[prov]
    return getModelMap(prov)[model]

def convertProvider(prov):
    if prov in ('best', 'random'):
        return prov
    return getProvMap()[prov].__name__

def findProvModel(model):
    if model[0] in ('random', 'best', 'ANY'):
        return model
    if model[1] in ('random', 'best'):
        return convertProvider(model[0]), model[1]
    prov = convertProvider(model[0])
    return prov, convertModel(prov, model[1])

class G4FProvider(BaseProvider):
    NAME = 'GPT4Free Provider'
    REPR = '<G4FProvider>'

    @staticmethod
    def stream(model, conv, opts):
        out = ''
        model = findProvModel(model)

        if model == ['random']:
            hierachy = G4FProvider.getHierachy()
            model = random.choice(hierachy)
            model = [model[0], random.choice(model[1])]
        
        if model in (['best'], ['ANY', 'best']):
            mods = g4f.models._all_models
            random.shuffle(mods)
            for i in mods:
                try:
                    yield from G4FProvider.stream(['ANY', i], conv, opts)
                    return
                except Exception:
                    pass
            yield format('ERROR: Every model tried errored! Sorry about that.', model, True)
            return
        
        if model[0] == 'ANY':
            if model[1] == 'random':
                model = [model[0], random.choice(g4f.models._all_models)]
            modelInf = g4f.models.__models__[model[1]][0]
            prov = modelInf.best_provider
            model[0] = 'ANY '+model[1]
            yield format('', [model[0], '???'])
        else:
            prov = g4f.Provider.__map__[model[0]]
            if model[1] == 'random':
                model = [model[0], random.choice(getProvModels(prov))]
            if model[1] == 'best':
                model = [model[0], None]
                yield format('', [model[0], '???'])
            else:
                yield format('', model)

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
                if hasattr(prov, 'last_provider'):
                    model[0] = prov.last_provider.__name__
                else: # TODO: replace window location for switching chats so it appears in history
                    model[0] = prov.__name__
                resp = i.choices[0].delta.content
                if resp:
                    out += resp
                yield format(out, model)
            yield format(out, model, True)
        else:
            yield format(resp.choices[0].delta.content, model, True)
    
    @staticmethod
    def getOpts(model):
        if 'random' in model:
            return []
        if 'best' in model:
            return []
        if model[0] == 'ANY':
            return []
        model = findProvModel(model)
        prov = g4f.Provider.__map__[model[0]]
        out = []
        typl = {
            'float': 'numInp',
            'int': 'numInp',
            'bool': 'boolInp',
        }
        typtransforml = {
            'float': float,
            'int': int,
            'bool': lambda x: x == 'True',
        }
        for op in prov.params.split('\n')[1:-1]:
            name, oth = op.split(':')
            oths = oth.split('=')
            typ, deflt = oths[0], (oths[1] if len(oths) > 1 else '')
            name, typ, deflt = name.strip(' '), typ.strip(' ,'), deflt.strip(' ,')
            if name not in ('model', 'messages', 'images', 'tools', 'stream'):
                if typ in typl:
                    o = {
                        'id': name,
                        'label': name[0].upper()+name[1:].replace('_', ' '),
                        'type': typl[typ]
                    }
                    if deflt not in ('', 'None'):
                        o['default'] = typtransforml[typ](deflt)
                    out.append(o)
        return out
    
    @staticmethod
    def getInfo(model):
        model = findProvModel(model)
        firstBest = False
        if model == ['random']:
            return 'You have selected a RANDOM model from GPT4Free!'
        elif model == ['best']:
            return 'You have chosen GPT4Free\'s best option; which will try every option available until one works!'
        elif model[0] == 'ANY':
            if model[1] == 'random':
                return 'You have selected a RANDOM model from GPT4Free!'
            elif model[1] == 'best':
                return 'You have chosen GPT4Free\'s best option; which will try every option available until one works!'
            
            return f'GPT4Free\'s `{model[1]}` model from `{g4f.models.__models__[model[1]][0].base_provider}` automatically tries every possible provider that provides the model!'
        prov = g4f.Provider.__map__[model[0]]
        secBest = model[1] == 'best'
        if secBest:
            model = [model[0], prov.default_model]
        # getattr(provider, "use_nodriver", False) ???
        return f"""`{model[0]}`'s {"*best* " if secBest else ""}model `{model[-1]}` is {"GPT4Free's *best*" if firstBest else "a GPT4Free"} model, which has the following properties:
{" - Label: "+prov.label+'\n' if hasattr(prov, 'label') else ''}\
{" - Parent: "+prov.parent+'\n' if hasattr(prov, 'parent') else ''}\
 - {'Does not require' if not prov.needs_auth else '**Requires**'} authentification{" at "+prov.login_url if hasattr(prov, 'login_url') else ''}
 - {'Supports' if prov.supports_stream else '**Does not support**'} streaming
 - {'Is' if model[-1] in getattr(prov, "image_models", []) else 'Is **not**'} an image model
 - {'Is' if model[-1] in getattr(prov, "vision_models", []) else 'Is **not**'} an vision model
 - located at {prov.url}"""
    
    @staticmethod
    def getHierachy():
        provs = getProvMap()
        return [['ANY', g4f.models._all_models]]+[i for i in [[name, list(getModelMap(prov).keys())] for name, prov in provs.items()] if i[1]]
