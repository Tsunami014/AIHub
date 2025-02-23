import g4f.Provider
from g4f.client import Client
from AIHub.providers.base import BaseProvider, format
import random
from string import printable

__all__ = ['G4FProvider']

PREFIX_LEN = 2

def format2(info, model, done=False):
    model = [stripEmoji(model[0]), stripEmoji(model[1])]
    return format(info, model, done)

def stripEmoji(s):
    return ''.join(filter(lambda x: x in printable, s))

def getMPrefxs(prov, model):
    img = "💬"
    if hasattr(prov, 'image_models'):
        if model in prov.image_models:
            img = "🖼️"
    if hasattr(prov, 'vision_models'):
        if model in prov.vision_models:
            img += "👀"
    return img

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
    prefix = ('🔒' if prov.needs_auth else '🔐')+("💬" if (not hasattr(prov, "image_models")) or any(i not in prov.image_models for i in models) else "")+("🖼️" if bool(getattr(prov, "image_models", False)) else "")+("👀" if bool(getattr(prov, "vision_models", False)) else "")
    return [prefix+name, [getMPrefxs(prov, i)+i for i in models]]

class G4FProvider(BaseProvider):
    NAME = 'GPT4Free Provider'
    REPR = '<G4FProvider>'
    @staticmethod
    def stream(model, conv, opts):
        out = ''
        model = [stripEmoji(i) for i in model]

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
            yield format2('', [model[0], '???'])
        else:
            prov = g4f.Provider.__map__[model[0]]
            if model[1] == 'random':
                try:
                    avmodels = prov.models
                except AttributeError:
                    avmodels = prov.get_models()
                model = [model[0], random.choice(avmodels)]
            if model[1] == 'best':
                model = [model[0], None]
                yield format2('', [model[0], '???'])
            else:
                yield format2('', model)

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
                yield format2(out, model)
            yield format2(out, model, True)
        else:
            yield format2(resp.choices[0].delta.content, model, True)
    
    @staticmethod
    def getOpts(model):
        if 'random' in model:
            return []
        if 'best' in model:
            return []
        if model[0] == 'ANY':
            return []
        model = [stripEmoji(i) for i in model]
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
        model = [stripEmoji(i) for i in model]
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
            
            return f'GPT4Free\'s {model[1]} model from {g4f.models.__models__[model[1]][0].base_provider} automatically tries every possible provider that provides the model!'
        prov = g4f.Provider.__map__[model[0]]
        secBest = model[1] == 'best'
        if secBest:
            model = [model[0], prov.default_model]
        # getattr(provider, "use_nodriver", False) ???
        return f"""{model[0]}'s {"best " if secBest else ""}model {model[-1]} is {"GPT4Free's best" if firstBest else "a GPT4Free"} model, which has the following properties:
{" - Label: "+prov.label+'\n' if hasattr(prov, 'label') else ''}\
{" - Parent: "+prov.parent+'\n' if hasattr(prov, 'parent') else ''}\
 - {'Does not require' if not prov.needs_auth else 'Requires'} authentification{" at "+prov.login_url if hasattr(prov, 'login_url') else ''}
 - {'Supports' if prov.supports_stream else 'Does not support'} streaming
 - {'Is' if model[-1] in getattr(prov, "image_models", []) else 'Is not'} an image model
 - {'Is' if model[-1] in getattr(prov, "vision_models", []) else 'Is not'} an vision model
 - located at {prov.url}"""
    
    @staticmethod
    def getHierachy():
        out = [getL(prov) for prov in g4f.Provider.__providers__]
        return [['ANY', g4f.models._all_models]]+[i for i in out if i[1]]
