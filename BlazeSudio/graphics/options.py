from dataclasses import dataclass, field
import pygame
import pygame.freetype
from string import printable

def Base(cls=None, default=True, modify_str=True):
    def wrap(clss):
        outcls = dataclass(clss, unsafe_hash=True, init=default, repr=default)
        if modify_str:
            def newstr(self):
                letters = str(self.__class__)[len('<class \'.')+len(self.__module__):-5]
                return f'<GO.{letters}{self.name} object>'
            outcls.__str__ = newstr
            outcls.__repr__ = newstr
            def newinit(func):
                def func2(self, *args, name='None', doc='', **kwargs):
                    self.name = name
                    self.__doc__ = doc
                    func(self, *args, **kwargs)
                return func2
            outcls.__init__ = newinit(outcls.__init__)
        return outcls
    if cls is None:
        # @Base()
        return wrap
    # @Base
    return wrap(cls)

# Colours
@Base(default=False, modify_str=False)
class C___(tuple):
    def __init__(self, colourtuple, name='C___'):
        self.name = name
    def __str__(self):
        return f'<GO.C{self.name} col=({str(list(self))[1:-1]})>'
    def __repr__(self): return str(self)
CTRANSPARENT = C___((255, 255, 255, 1), name='TRANSPARENT')
CWHITE =  C___((255, 255, 255), name='WHITE')
CAWHITE = C___((200, 200, 200), name='ALMOSTWHITE')
CGREEN =  C___((60, 200, 100),  name='GREEN')
CRED =    C___((255, 60, 100),  name='RED')
CBLUE =   C___((60, 100, 255),  name='BLUE')
CBLACK =  C___((0, 0, 0),       name='BLACK')
CYELLOW = C___((255, 200, 50),  name='YELLOW')
CGREY =   C___((125, 125, 125), name='GREY')
def CNEW(name):
    c = pygame.color.Color(name)
    return C___((c.r, c.g, c.b), name=name)
CINACTIVE = CNEW('lightskyblue3')
CACTIVE =   CNEW('dodgerblue2')

def CRAINBOW():
    l = [
        CRED,
        CNEW('orange'),
        CYELLOW,
        CGREEN,
        CBLUE,
        CNEW('pink'),
        CNEW('purple'),
        CGREY,
        CACTIVE
    ]
    while True:
        for i in l: yield i

# font Sides
# Weighting
@Base
class SW__:
    w: int
SWLEFT =  SW__(0,   name='LEFT')
SWTOP =   SW__(0,   name='TOP')
SWMID =   SW__(0.5, name='MIDDLE')
SWBOT =   SW__(1,   name='BOTTOM')
SWRIGHT = SW__(1,   name='RIGHT')
# Direction
@Base
class SD__:
    idx: int
SDLEFTRIGHT = SD__(0, name='LEFT-RIGHT')
SDUPDOWN =    SD__(1, name='UP-DOWN')

# Fonts
class F___:
    def __init__(self, name, size, bold=False, italic=False):
        self.font = pygame.font.SysFont(name, size, bold, italic)
        self.emojifont = pygame.freetype.SysFont('segoeuisymbol', size, bold, italic)
    def render(self, txt, col, updownweight=SWMID, leftrightweight=SWMID, allowed_width=None, renderdash=True, maxlines=None, allowed_height=None, return_output=False):
        """
        Renders some text with emoji support!

        Parameters
        ----------
        txt : str
            The text to render!
        col : tuple[int,int,int]
            The colour of the text
        updownweight : GO.SW___, optional
            The weight of the text up-down; make the text weighted towards the top, middle, or bottom, by default SWMID
            You probably do not want to change this
        leftrightweight : GO.SW___, optional
            The weight of the text left-right, by default SWMID
            This only ever comes into effect if allowed_width is not None and there is enough text to span multiple lines
            You probably want to change this occasionally
        allowed_width : int, optional
            The allowed width of the text, by default None
            If the text goes over this amount of pixels, it makes a new line
            None disables it
        
        Other parameters:
        ----------------
        renderdash : bool, optional
            Whether or not to render the '-' at the end of lines of text that are too big to fit on screen, by default True
        maxlines : int, optional
            The maximum number of lines to render if the text will be split over newlines, defaults to all of them
        allowed_height : int, optional
            The allowed height of the text, by default None
            If the text's total height is above this, then it stops making more text
        return_output : bool, optional
            Whether to return the string as it is shown on screen or not, by default False
            This will output (for example) "hello I am \nsuuuuuuuuuuuuu-\nuuuper cool"

        Returns
        -------
        pygame.Surface | tuple[pygame.Surface, str]
            The surface of the text! See return_output for the second thing it can return
        """
        if txt == '':
            if return_output:
                return pygame.Surface((0, 0)), ''
            return pygame.Surface((0, 0))
        if allowed_width is None:
            out = self.combine(self.split(txt, col), weight=updownweight)
            if return_output:
                return out, txt
            return out
        else:
            masterlines = []
            for l in txt.strip('\n').split('\n'):
                # Thanks to https://stackoverflow.com/questions/49432109/how-to-wrap-text-in-pygame-using-pygame-font-font for the font wrapping thing
                # Split text into words
                words = l.split(' ')
                # now, construct lines out of these words
                lines = []
                while len(words) > 0:
                    # get as many words as will fit within allowed_width
                    line_words = []
                    while len(words) > 0:
                        line_words.append(words.pop(0))
                        fw, fh = self.size(' '.join(line_words + words[:1]))
                        if fw > allowed_width:
                            break
                    # add a line consisting of those words
                    line = ' '.join(line_words)
                    if len(line_words) == 1 and self.size(line_words[0])[0] > allowed_width:
                        out = []
                        line = ''
                        for i in line_words[0]:
                            if renderdash:
                                fw, fh = self.size(line+'---')
                                if fw > allowed_width:
                                    out.append(line+'-')
                                    line = i
                                else:
                                    line += i
                            else:
                                fw, fh = self.size(line+'--')
                                if fw > allowed_width:
                                    out.append(line)
                                    line = i
                                else:
                                    line += i
                        #if line != '': out.append(line)
                        lines.extend(out)
                    lines.append(line)
                masterlines.extend(lines)
            
            surs = []
            h = 0
            for i in masterlines[:maxlines]:
                sur = self.combine(self.split(i, col), updownweight)
                if allowed_height is not None:
                    if sur.get_height() + h > allowed_height:
                        break
                    h += sur.get_height()
                surs.append(sur)
            out = self.combine(surs, leftrightweight, SDUPDOWN)
            if return_output:
                return out, '\n'.join(masterlines[:maxlines][:len(surs)])
            return out
    
    def split(self, txt, col):
        """
        Splits text and renders it!
        This splits text up into 2 different parts:
        The part with regular renderable text and the part without (i.e. emojis, other stuff)
        It then uses the 2 different fonts, one for rendering text and the other for non-text
        And renders them all seperately and then makes a list of the outputs!

        Parameters
        ----------
        txt : str
            The text to split
        col : tuple[int,int,int]
            The colour of the text

        Returns
        -------
        list[pygame.Surface]
            A list of pygame surfaces of all the different texts rendered!
            You can use `FNEW.combine(surs)` to combine the surfaces!
        """
        parts = []
        part = ''
        prtable = None
        for i in list(txt)+[None]:
            if i is not None:
                isprt = (i in printable)
            else:
                isprt = not prtable # Assuming it has been set with something that is an actual character
            if prtable is None:
                prtable = isprt
            if isprt != prtable and i != ' ':
                if prtable:
                    parts.append(self.font.render(part, 1, col))
                else:
                    parts.append(self.emojifont.render(part, col)[0])
                part = ''
                if i is not None:
                    prtable = isprt
            if i is not None:
                part += i
        return parts
    
    def combine(self, surs, weight=SWMID, dir=SDLEFTRIGHT):
        """
        Combines multiple surfaces into one!

        Parameters
        ----------
        surs : list[pygame.Surface]
            The list of surfaces to combine!
        weight : GO.SW___, optional
            The weight of the combine, i.e. make al the text from left to right, centred, etc., by default SWMID
        dir : GO.SD___, optional
            The direction of the combine; i.e. combine all the texts into one long text or make them all have new lines, by default SDLEFTRIGHT

        Returns
        -------
        pygame.Surface
            The combined surface!
        """
        if dir == SDLEFTRIGHT:
            sze = (sum([i.get_width() for i in surs]), max([i.get_height() for i in surs]))
        else:
            sze = (max([i.get_width() for i in surs]), sum([i.get_height() for i in surs]))
        sur = pygame.Surface(sze).convert_alpha()
        sur.fill((255, 255, 255, 1))
        pos = 0
        for i in surs:
            if dir == SDLEFTRIGHT:
                sur.blit(i.convert_alpha(), (pos, (sze[1]-i.get_height())*weight.w))
                pos += i.get_width()
            else:
                sur.blit(i.convert_alpha(), ((sze[0]-i.get_width())*weight.w, pos))
                pos += i.get_height()
        return sur  
    
    def size(self, txt):
        """
        Gets the size of the font if you render a certain text!

        Parameters
        ----------
        txt : str
            The text to render and see the size of

        Returns
        -------
        tuple[int,int]
            The size of the output font
        """
        surs = self.split(txt, (0, 0, 0))
        return (sum([i.get_width() for i in surs]), max([i.get_height() for i in surs]))
    
    def maxsize(self):
        """
        Gets the maximum rendered size of any text, excluding emojis

        Returns
        -------
        tuple[int,int]
            The maximum size this font can ever produce (excluding emojis)
        """
        return self.font.render(printable, 1, (0, 0, 0)).get_size()

class FNEW(F___): pass # Making new fonts

FTITLE =    F___('Comic Sans MS', 64, True, name='TITLE')
FCODEFONT = F___('Lucida Sans Typewriter', 16, name='CODE-FONT')
FFONT =     F___(None, 52, name='FONT')
FSMALL =    F___(None, 32, name='SMALL')

# Positions
@Base
class P___:
    idx: int
    lmr: int | None # Left(0) Middle(1) Right(2)
    umd: int | None # Up(0) Middle(1) Down(2)

PLTOP =    P___(0, 0, 0, name='LEFTTOP')
PLCENTER = P___(1, 0, 1, name='LEFTCENTER')
PLBOTTOM = P___(2, 0, 2, name='LEFTBOTTOM')
PCTOP =    P___(3, 1, 0, name='CENTERTOP')
PCCENTER = P___(4, 1, 1, name='CENTERCENTER')
PCBOTTOM = P___(5, 1, 2, name='CENTERBOTTOM')
PRTOP =    P___(6, 2, 0, name='RIGHTTOP')
PRCENTER = P___(7, 2, 1, name='RIGHTCENTER')
PRBOTTOM = P___(8, 2, 2, name='RIGHTBOTTOM')
PFILL =    P___(9, None, None, name='FILL')

# Stacks. Don't use unless you know what you're doing
PSTACKS = {
    PLTOP:    ([1, 0],  lambda size, sizeofobj: (0, 0)),
    PLCENTER: ([1, 0],  lambda size, sizeofobj: (0, round(size[1]/2-sizeofobj[1]/2))),
    PLBOTTOM: ([1, 0],  lambda size, sizeofobj: (0, size[1]-sizeofobj[1])),
    PCTOP:    ([0, 1],  lambda size, sizeofobj: (round(size[0]/2-sizeofobj[0]/2), 0)),
    PCCENTER: ([0, 1],  lambda size, sizeofobj: (round(size[0]/2-sizeofobj[0]/2), round(size[1]/2-sizeofobj[1]/2))),
    PCBOTTOM: ([0, -1], lambda size, sizeofobj: (round(size[0]/2-sizeofobj[0]/2), size[1]-sizeofobj[1])),
    PRTOP:    ([-1, 0], lambda size, sizeofobj: (size[0]-sizeofobj[0], 0)),
    PRCENTER: ([-1, 0], lambda size, sizeofobj: (size[0]-sizeofobj[0], round(size[1]/2-sizeofobj[1]/2))),
    PRBOTTOM: ([-1, 0], lambda size, sizeofobj: (size[0]-sizeofobj[0], size[1]-sizeofobj[1])),
    PFILL:    ([0, 0],  lambda size, sizeofobj: (0, 0))
}

PIDX = 0 # DO NOT USE UNLESS YOU REALLY KNOW WHAT YOU'RE DOING

def PNEW(stack, func, idx=None, lmr=None, umd=None):
    """
    Create new layouts!

    Parameters
    ----------
    stack : list[int,int]
        The stacking of the elements;
        i.e. will a new element using the same function be placed left of the original, or above it, or...
        The first element in the list is the x position offset (1, 0 or -1) and the second value is the y (1, 0 or -1)
    func : function(sizeofscreen: tuple[int,int], sizeofobj: tuple[int,int]); returns tuple[int,int]
        The function of the layout; returns where to put the element
    idx : int, optional
        The ID of the new P___, by default None
        You probably should never need to use this unless you want to replace an old position with a new one
    lmr : int, optional
        Whether this layout goes to the Left of the screen (0), Middle (1), Right (2), or N/A (None), by default None
        This is optional, and does nothing except help give your new layout some documentation of sorts
    umd : int, optional
        The same as above but with Up (0), Middle (1), Down (2), and N/A (None), by default None

    Returns
    -------
    GO.P___
        The output position!
    """
    # TODO: Make this able to take an existing P___ as func and work out the function itself
    global PIDX
    if idx == None:
        idx = PIDX
        PIDX += 1
    pos = P___(idx+10, lmr, umd)
    PSTACKS[pos] = (stack, func)
    return pos

def PSTATIC(x, y, idx=None):
    """
    Creates a GO.P___ to put stuff at a specific x and y location

    Parameters
    ----------
    x : int
        The x position of where to put the element
    y : int
        The y position of where to put the element
    idx : int, optional
        The ID of the new P___, by default None
        You probably should never need to use this unless you want to replace an old position with a new one

    Returns
    -------
    GO.P___
        The output position!
    """
    global PIDX
    if idx == None:
        idx = PIDX
        PIDX += 1
    pos = P___(idx+10, None, None)
    PSTACKS[pos] = ([0, 0], lambda _, __: (x, y))
    return pos

# Events
@Base
class E___:
    idx: int
    passed: dict = field(default_factory=dict)

EFIRST =        E___(0, name='FIRST',  doc='The first event, before the screen has even displayed it\'s first frame')
ELOADUI =       E___(1, name='LOADUI', doc='Every time it loads the UI (first, when G.Refresh, etc.) it calls this function.')
ETICK =         E___(2, name='TICK',   doc='Each tick this is ran')
EELEMENTCLICK = E___(3, name='ELEMENTCLICK', doc='When an element is clicked, this is ran', passed={'element': 'The element that got clicked'})
EEVENT =        E___(4, name='EVENT',  doc='When a pygame event occurs (click mouse, press button, etc.)', passed={'element': 'The pygame.event.Event that occured'})
ELAST =         E___(5, name='LAST',   doc='Just before quitting this is ran', passed={'aborted': 'Whether or not the graphic screen was aborted due to G.Abort()'})

# Types
@Base
class T___:
    idx: int
TBUTTON =   T___(0, name='BUTTON')
TTEXTBOX =  T___(1, name='TEXTBOX')
TINPUTBOX = T___(2, name='INPUTBOX')
TSWITCH =   T___(3, name='SWITCH')

# Resizes
@Base
class R___:
    idx: int
RWIDTH =  R___(0, name='WIDTH')
RHEIGHT = R___(1, name='HEIGHT')
RNONE =   R___(2, name='NONE')
