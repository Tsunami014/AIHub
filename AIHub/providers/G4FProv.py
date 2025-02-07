import g4f.Provider
from g4f.client import Client
from AIHub.providers.base import BaseProvider, format

class G4FProvider(BaseProvider):
    NAME = 'GPT4Free Provider'
    REPR = '<G4FProvider>'
    @staticmethod
    def stream(model, conv):
        out = ''
        prov = g4f.Provider.__map__[model[0][1:]]
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
                    yield format(out)
                yield format(out, True)
            else:
                yield format(resp.choices[0].delta.content)
                yield format(resp.choices[0].delta.content, True)
        except Exception as e:
            yield format(out)
            yield format(f'{out}{"\n" if out != "" else ""}Sorry, but an error has occured: {e}', True)
    
    @staticmethod
    def getInfo(model):
        prov = g4f.Provider.__map__[model[0][1:]]
        return f"""{model[0][1:]}'s model {model[-1]} is a GPT4Free model, which has the following properties:
 - {'Does not require' if not prov.needs_auth else 'Requires'} authentification to work
 - {'Supports' if prov.supports_stream else 'Does not support'} streaming
 - located at {prov.url}"""
    
    @staticmethod
    def getHierachy():
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
        out = [getL(prov) for prov in g4f.Provider.__providers__]
        return [i for i in out if i[1]]
