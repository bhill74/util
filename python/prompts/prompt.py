"""
Prompt

The module that allows creation of different types of user input prompts
"""

import sys
import re
import os
import subprocess


# Patterns to use
_neg = re.compile('^!(\d+)$')
_range = re.compile('^(\d+)\-(\d+)$')
_neg_range = re.compile('^!(\d+)\-(\d+)$')
_column_pattern = re.compile('COLUMNS=(\d+)')
_line_pattern = re.compile('LINES=(\d+)')


def _get_range_base(val, pattern):
    if not re.match(pattern, val):
        return [], False

    l, h = re.findall(pattern, val)[0]
    l = int(l)
    h = int(h)
    if l == h:
        return [l], True

    if l < h:
       return [i for i in range(l, h+1)], True

    return [], False

def _get_range(val):
    if isinstance(val, int):
        return [val], True 
    
    if isinstance(val, str):
        if val.isnumeric():
            return [int(val)], True

    return _get_range_base(val, _range)

def _get_neg_range(val):
    if re.match(_neg, val):
        return [int(val[1:])], True

    return _get_range_base(val, _neg_range)


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    """Unix implememntation of Getch"""
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    """Windows implementation of Getch"""
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


def _format(code):
    """Escapes the formatting code"""
    return '\033[{}m'.format(code)


class Base:
    OK          = 0
    CANCEL      = 1
    ERROR       = 2

    """The base class for all user input prompts"""
    def __init__(self, out=None, title=None, prompt=None, default=None):
        self._default = None
        if default:
            self._default = default if isinstance(default, list) else [default]

        self._title = title
        self._prompt = prompt if (prompt) else "Choice"
        self._out = out if out else sys.stdout
        self._base_colour = 2

    def colour(self, colour):
        self._base_colour = colour

    def _formatting(self):
        return {'bracket': _format(self._base_colour + 30),
                'choice':  _format(self._base_colour + 90),
                'reset':   _format('')}

    def title(self, title=None):
        if title:
            self._title = title

        return self._title

    def default(self, default=None):
        if default:
            if isinstance(default, list):
                self._default = default
            else:
                self._default = [default]

        return self._default

    def prompt(self, prompt=None):
        if prompt:
            self._prompt = prompt

        return self._prompt

    def write(self, text):
        self._out.write(text)

    def parse(self, selection):
        return selection, Base.OK

    def show_prompt(self):
        default = ",".join(self._default) if self._default else None
        self.write("{}{}: ".format(self._prompt, " ({})".format(default) if default else ""))

    def preamble(self):
        return

    def error(self):
        self.write(" Problem with the submission\n")

    def filter(self, answer):
        return answer

    def validate(self):
        read_in = open("/dev/tty", 'r')

        while True:
            self.show_prompt()
            self._out.flush()
            ans = None 
            code = Base.ERROR
            try:
                inpt = read_in.readline().rstrip()
                ans, code = self.parse(inpt)
            except Exception as e:
                #print(str(e))
                ans = None

            if code == Base.CANCEL:
                return None
            elif code == Base.ERROR or ans is None:
                self.error()
            else:
                return self.filter(ans) 

    def get(self):
        if (self._title):
            self.write("{}\n".format(self._title))
        self.preamble()
        return self.validate()


class EntryBase(Base):
    """
    EntryBase

    The base class for all inputs that accept a flexible user input
    """

    def __init__(self, out=None):
        Base.__init__(self, out=out)
        self._prompt = "Entry"

    def error(self):
        self.write(" Please make a valid entry\n")


class ChoiceBase(Base):
    """
    ChoiceBase

    The base class for all inputs that offer a fixed set of choices
    """

    def __init__(self, out=None, title=None, prompt=None, default=None, choices=None):
        Base.__init__(self, out=out, title=title,
                      prompt=prompt if prompt else "Choice",
                      default=default)
        self._choices = choices if choices else []

    def choices(self, choices=None):
        if choices:
            self._choices = choices

        return self._choices

    def parse(self, selection):
        if selection == "":
            if self._default:
                return self._default, Base.OK

            return None, Base.ERROR

        c = self.choices()
        val = int(selection)
        if val < 1 or val > len(c):
            return None, Base.ERROR

        return c[val-1], Base.OK

    def show_prompt(self):
        default = ",".join(self._default) if self._default else None
        self.write("{}{}: ".format(self._prompt, " ({})".format(default) if default else ""))

    def error(self):
        self.write(" Please make a valid choice\n")


class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class SelectionBase(ChoiceBase):
    """
    SelectionBase

    The base class for all inputs that offer a selection of choices in menu form
    and are chosen using the corresponding index.
    """

    def __init__(self, out=None, prompt=None, title=None, default=None, choices=None):
        ChoiceBase.__init__(self, out=out,
                            prompt=prompt,
                            title=title if title else "Select from options",
                            default=default,
                            choices=choices)

    def decorate_op(self, i):
        return ''

    def decorate_op_fmt(self):
        return 0

    def decorate_op_size(self):
        return self.__dict__.update(kwargs)

    def preamble(self):
        c = self.choices()
        n = len(c)
        ms = max(len(ch) for ch in c)
        osize = ms + 2
        slot = ms + len(str(n)) + 5
        slot += self.decorate_op_size() 
        osize += self.decorate_op_size()

        try:
            ts = os.get_terminal_sizei()
        except:
            process = subprocess.Popen(['resize'], stdout=subprocess.PIPE, universal_newlines=True)
            resize = process.stdout.read()
            columns = re.findall(_column_pattern, resize)[0]
            lines = re.findall(_line_pattern, resize)[0]
            ts = Namespace(lines=int(lines), columns=int(columns))

        mrow = ts.lines
        if ts.lines > n:
            col = 1
            row = n
        else:
            col = int((ts.columns - 1)/slot)
            row = int((n + col - 1)/col)
    
        title_lines = self._title.split("\n")
        used = len(title_lines)
        used += sum([int((len(t)+1)/ts.columns) for t in title_lines])

        block = row
        trim = False
        if row > mrow:
            block = mrow - 2
            trim = True

        r = 0
        blocks = [(r, block-used if trim else block)]
        r += blocks[-1][1]
        while r < row:
            if r + block < row:
                segment = block
            else:
                segment = row - (blocks[-1][0] + blocks[-1][1])

            blocks.append((r, segment))
            r += segment

        fmt = self._formatting()
        add_len = len(fmt['bracket'])*2 + len(fmt['choice']) + len(fmt['reset'])*2
        add_len += self.decorate_op_fmt()

        def is_selected(val):
            return True if val in self._default else False


        for rb in blocks:
            r = rb[0]
            segment = rb[1]
            last = False if r + segment < row else True

            for j in range(segment):
                line = []
                for i in range(col):
                    index = j + i*segment + r*col
                    dec = self.decorate_op(index)
                    op = "{}[{}{}{}{}]{}".format(
                            fmt['bracket'], fmt['reset'] + fmt['choice'],
                            index+1, dec,
                            fmt['bracket'], fmt['reset'])
                    #op = f'{op:>{osize + add_len}}'
                    op = '{:>{osize + add_len}}'.format(op)
                    if index < n:
                        m = "{} {}".format(op, c[index])
                        #line.append(f'{m:<{slot + add_len}}')
                        line.append('{:<{slot + add_len}}'.format(m))
                    else:
                        line.append(" ")

                self.write("".join(line) + "\n")

            if not last:
                self.write("<Press Any Key to Continue>...\n")
                _Getch()()


class ChoicePrompt(ChoiceBase):
    """
    ChoicePrompt

    The base class for user inputs that have a fixed set of choices and are chosen
    by matching the text
    """

    def __init__(self, options, out=None, prompt=None, default=None):
        ChoiceBase.__init__(self, out=out, prompt=prompt, title=None, default=default)
        ChoiceBase.choices(self, options)
        self._title = None

    def choices(self, choices=None):
        if (choices):
            print("Cannot change the choices")
        return self._choices

    def parse(self, selection):
        if len(selection) == 0:
            if self._default:
                return self._default, Base.OK
           
            return None, Base.ERROR

        c = self.choices()
        result = []
        for i in range(len(c)):
            if c[i].lower().startswith(selection.lower()):
                result.append(c[i])

        if len(result) != 1:
            return None, Base.ERROR

        return result, Base.OK

    def show_prompt(self):
        fmt = self._formatting()
        default = ",".join(self._default) if self._default else None

        ops = ["{}{}{}{}".format(fmt['choice'], c[0], fmt['reset'], c[1:]) for c in self.choices()]
        self.write("{}{} {}[{}{}{}]{}: ".format(self._prompt, " ({})".format(default) if default else "", fmt['bracket'], fmt['reset'], "/".join(ops), fmt['bracket'], fmt['reset']))

    def get(self):
        r = Base.get(self)
        if isinstance(r, list):
            return r[0] if len(r) else None 

        return r


class StringEntry(EntryBase):
    """
    StringEntry

    Creates a user input to capture any non-empty text string
    """

    def __init__(self, out=None):
        EntryBase.__init__(self, out=out)


class IntegerEntry(EntryBase):
    """
    IntegerEntry

    Creates a user input to capture any integer value
    """

    def __init__(self, out=None):
        EntryBase.__init__(self, out=out)

    def parse(self, selection):
        return selection if (int(selection) or selection == '0') else '', Base.OK


class YesNoPrompt(ChoicePrompt):
    """
    YesNoPrompt

    Creates a user input where the desired response is 'Yes' or 'No'
    """

    def __init__(self, out=None, prompt=None, default=None):
        ChoicePrompt.__init__(self, ["Yes", "No"], out=out, prompt=prompt, default=default)


class TrueFalsePrompt(ChoicePrompt):
    """
    TrueFalsePrompt

    Creates a user input where the desired response is 'True' or 'False'
    """

    def __init__(self, out=None, prompt=None, default=None):
        ChoicePrompt.__init__(self, ["True", "False"], out=out, prompt=prompt, default=default)


class SingleSelectionPrompt(SelectionBase):
    """
    SingleSelectionPrompt

    Creates a user input of a selection of choices where only one may be chosen
    """

    def __init__(self, out=None):
        SelectionBase.__init__(self, out=out)

    def get(self):
        return SelectionBase.get(self)[0]


class MultipleSelectionPrompt(SelectionBase):
    """
    MultipleSelectionPrompt

    Creates a user input of a selection of choices where many options can be chosen at once 
    """

    def __init__(self, out=None, prompt=None, title=None, default=None, choices=None):
        SelectionBase.__init__(self, out=out,
                               prompt=prompt,
                               title=title,
                               default=default,
                               choices=choices)

    def parse(self, selection):
        if (selection == ""):
            if self._default:
                return self._default, Base.OK

            return None, Base.ERROR

        c = self.choices()
        n = len(c)
        result = []
        for s in selection.replace(' ', '').split(","):
            r, v = _get_range(s)
            if v:
                if min(r) < 0 or max(r) > n:
                    return None, Base.ERROR

                result += [c[i-1] for i in r] 
                continue

            return None, Base.ERROR 

        return result, Base.OK


class CheckboxPrompt(MultipleSelectionPrompt):
    """
    CheckboxPrompt

    Creates a user input of a selection of choices and will repeatedly re-display the selections
    until finalized
    """

    OPTIONS = ['All', 'Clear', 'Ok', 'Quit']

    def __init__(self, out=None, prompt=None, title=None, default=None, choices=None):
        MultipleSelectionPrompt.__init__(self, out=out,
                                         prompt=prompt,
                                         title=title,
                                         default=default,
                                         choices=choices)
        self._value = default if default else None 
        if choices and not self._value:
            self._value = []

        self._is_done = False
        self._options = ['All', 'Clear', 'Ok', 'Quit']

    def _formatting(self):
        fmt = MultipleSelectionPrompt._formatting(self)
        fmt['selected'] = _format(31)
        return fmt

    def default(self,value):
        MultipleSelectionPrompt.default(self, value)
        self._value = value

    def parse(self, selection):
        if selection == "":
            return None, Base.ERROR

        sel = selection.lower()
        c = self.choices()

        # All
        if self._options[0].lower().startswith(sel):
            return c, Base.OK

        # Clear 
        elif self._options[1].lower().startswith(sel):
            return [], Base.OK

        # OK
        elif self._options[2].lower().startswith(sel):
            self._is_done = True
            return self._value, Base.OK

        # Quit
        elif self._options[3].lower().startswith(sel):
            self._is_done = True
            return None, Base.CANCEL

        n = len(c)
        add = []
        remove = []
        for s in selection.replace(' ', '').split(","):
            r, v = _get_range(s)
            if v:
                if min(r) < 0 or max(r) > n:
                    return None, Base.ERROR

                add += r
                continue

            r, v = _get_neg_range(s)
            if v:
                if min(r) < 0 or max(r) > n:
                    return None, Base.ERROR

                remove += r
                continue

            return None, Base.ERROR

        result = []
        c = self.choices()
        for i in range(len(c)):
            if i+1 in add:
                result.append(c[i])
            elif i+1 in remove:
                continue
            elif c[i] in self._value:
                result.append(c[i])

        return result, Base.OK

    def show_prompt(self):
        fmt = self._formatting()

        ops = ["{}{}{}{}".format(fmt['choice'], c[0], fmt['reset'], c[1:]) for c in self._options] + ['#','!#']
        self.write("{} {}[{}{}{}]{}: ".format(self._prompt, fmt['bracket'], fmt['reset'], "/".join(ops), fmt['bracket'], fmt['reset']))

    def decorate_op(self, i):
        c = self.choices()
        fmt = self._formatting()
        return "{}{} {}{}".format(fmt['reset'], fmt['selected'], 'X' if c[i] in self._value else ' ', fmt['reset'])

    def decorate_op_size(self):
        return 2

    def decorate_op_fmt(self):
        fmt = self._formatting()
        return len(fmt['selected']) + len(fmt['reset'])*2

    def get(self):
        while True:
            if (self._title):
                self.write("{}\n".format(self._title))
            self.preamble()
            result = self.validate()
            if self._is_done:
                return result 

            self._value = result
