import g4f.Provider
from g4f.client import Client
from AIHub.providers.base import BaseProvider, format
import random
import time
import asyncio

__all__ = ['G4FProvider']

def timeCache(func, wait=60*5): # 60*5 = 5 mins
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

def getMPrefxs(provs, model):
    img = ["🖼️", "👀"]
    for prov in provs:
        if img[0] == "🖼️" and model not in getattr(prov, 'image_models', []):
            img[0] = "💬"
        if "👀" in img and model not in getattr(prov, 'vision_models', []):
            img.remove("👀")
    return "".join(img)

@timeCache
def getProvModels(prov):
    aliases = getattr(prov, 'model_aliases', {}).copy()
    aliases.update(getattr(prov, 'models_aliases', {}))
    try:
        models = prov.get_models()
    except Exception:
        models = getattr(prov, 'models', [])
    models += aliases.values()
    return list({i: None for i in models}.keys()), aliases

@timeCache
def getDecorProvModels(prov):
    models, aliases = getProvModels(prov)
    aliasesRev = {j: i for i, j in aliases.items()}
    return [f'{getMPrefxs([prov], i)} {(aliasesRev[i] if i in aliasesRev else i)}<*sep*>{i}' for i in models]

def getProvName(prov):
    models, _ = getProvModels(prov)
    name = getattr(prov, 'label', prov.__name__)
    prefix = ('🔒' if prov.needs_auth else '🔐')+("💬" if (not hasattr(prov, "image_models")) or any(i not in prov.image_models for i in models) else "")+("🖼️" if bool(getattr(prov, "image_models", False)) else "")+("👀" if bool(getattr(prov, "vision_models", False)) else "")
    return prefix+' '+name

class G4FProvider(BaseProvider):
    NAME = 'GPT4Free Provider'
    REPR = '<G4FProvider>'

    @classmethod
    def stream(cls, model, conv, opts):
        out = ''

        if model == ['random']:
            hierachy = G4FProvider.getHierachy()
            alls = [[i[0],j] for i in hierachy for j in i[1]]
            random.shuffle(alls)
            for i in alls:
                if '<*sep*>' in i[0]:
                    i[0] = i[0][i[0].index('<*sep*>')+7:]
                if '<*sep*>' in i[1]:
                    i[1] = i[1][i[1].index('<*sep*>')+7:]
                try:
                    yield from G4FProvider.stream(i, conv, opts)
                    return
                except Exception:
                    pass
            yield format('ERROR: Every model tried errored! Sorry about that.', model, True)
            return
        
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
                model = [model[0], random.choice(getProvModels(prov)[0])]
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
            **{i: j for i, j in opts.items() if j is not None}
        )
        if strem:
            for i in resp:
                if hasattr(prov, 'last_provider'):
                    model[0] = prov.last_provider.__name__
                else:
                    model[0] = prov.__name__
                resp = i.choices[0].delta.content
                if resp:
                    out += resp
                yield format(out, model)
            yield format(out, model, True)
        else:
            yield format(resp.choices[0].delta.content, model, True)
    
    @classmethod
    def getOpts(cls, model):
        if 'random' in model:
            return []
        if model in (['best'], ['ANY', 'best']):
            return []
        prov = None
        if model[1] == 'best':
            prov = g4f.Provider.__map__[model[0]]
            model = [model[0], prov.default_model]
        if model[0] == 'ANY':
            provs = g4f.models.__models__[model[1]][1]
            allps = []
            defs = {}
            for p in provs:
                o = []
                pars = p.params.split('\n')[1:-1]
                for i in pars:
                    nme, xtra = i.split(':')
                    typ, *d = xtra.split('=')
                    if d:
                        df = d[0].strip(' ,')
                        if nme not in defs:
                            defs[nme] = df
                        elif defs[nme] != df:
                            defs[nme] = 'None'
                    o.append(nme.strip(' ')+':'+typ.strip(' ,'))
                allps.append(o)
            params = []
            for p in allps[0]:
                if all(p in j for j in allps[1:]):
                    nme, _ = p.split(':')
                    if nme in defs and defs[nme] != 'None':
                        params.append(p+'='+defs[nme])
                    else:
                        params.append(p)
        else:
            prov = prov or g4f.Provider.__map__[model[0]]
            params = prov.params.split('\n')[1:-1]
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
        for op in params:
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
    
    @classmethod
    def getInfo(cls, model):
        def props(prov):
            return f"""
{" - Label: "+prov.label+'\n' if hasattr(prov, 'label') else ''}\
{" - Parent: "+prov.parent+'\n' if hasattr(prov, 'parent') else ''}\
 - {'Does not require' if not prov.needs_auth else '**Requires**'} authentification{" at "+prov.login_url if getattr(prov, 'login_url', None) is not None else ''}
 - {'Supports' if prov.supports_stream else '**Does not support**'} streaming
 - {'Is' if model[-1] in getattr(prov, "image_models", []) else 'Is **not**'} an image model
 - {'Is' if model[-1] in getattr(prov, "vision_models", []) else 'Is **not**'} a vision model
 - located {"at "+prov.url if prov.url is not None else "nowhere..."}
"""[:-1]
        firstBest = False
        if model == ['random']:
            return 'You have selected a RANDOM model from GPT4Free! This tries every model in a random order until one works!'
        elif model == ['best']:
            return 'You have chosen GPT4Free\'s best option; which will try every option available until one works!'
        elif model[0] == 'ANY':
            if model[1] == 'random':
                return 'You have selected a RANDOM model from GPT4Free!'
            elif model[1] == 'best':
                return 'You have chosen GPT4Free\'s best option; which will try every option available until one works!'
            
            return f'GPT4Free\'s `{model[1]}` model from `{g4f.models.__models__[model[1]][0].base_provider}` automatically tries every possible provider that provides the model!\n\
It is served by {len(g4f.models.__models__[model[1]][1])} providers.\nIt has the following properties:'+props(g4f.models.__models__[model[1]][0].best_provider)
        prov = g4f.Provider.__map__[model[0]]
        secBest = model[1] == 'best'
        if secBest:
            model = [model[0], prov.default_model]
        # getattr(provider, "use_nodriver", False) ???
        return f'`{model[0]}`\'s {"*best* " if secBest else ""}model `{model[-1]}` is {"GPT4Free's *best*" if firstBest else "a GPT4Free"} model, which has the following properties:'+props(prov)
    
    @classmethod
    async def _getHierachy(cls):
        model_tasks = [
            asyncio.to_thread(getMPrefxs, ms[1], name)
            for name, ms in g4f.models.__models__.items()
        ]
        model_prefixes = await asyncio.gather(*model_tasks)
        
        models_part = []
        for (name, ms), prefix in zip(g4f.models.__models__.items(), model_prefixes):
            models_part.append(f'{prefix} {name}<*sep*>{name}')
        
        models_list = [['ANY', models_part]]
        
        # Process provider tasks concurrently
        valid_providers = [prov for prov in g4f.Provider.__providers__ if prov.working]
        decor_tasks = [asyncio.to_thread(getDecorProvModels, prov) for prov in valid_providers]
        decor_results = await asyncio.gather(*decor_tasks)
        
        provider_results = []
        for prov, decor_models in zip(valid_providers, decor_results):
            if decor_models:
                prov_name = await asyncio.to_thread(getProvName, prov)
                provider_results.append([f'{prov_name}<*sep*>{prov.__name__}', decor_models])
        
        return models_list + provider_results

    @classmethod
    @timeCache
    def getHierachy(cls):
        return asyncio.run(cls._getHierachy())
