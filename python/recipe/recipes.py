import subprocess
import sys
import select
import re
import shlex
import glob
import os
import pdb

# Personal modules
sys.path.append(os.path.join(os.getenv('HOME'), "lib", "prompts"))
import prompt


def add_formatting(text, codes=[]):
    if not codes or len(codes) == 0:
        return text

    return "\033[{}m{}\033[m".format(";".join([str(c) for c in codes]), text)

def replace_history(cmd, history):
    def subst(m):
        if not history:
            return "<empty>"
        i = int(m[1])
        if i >= len(history):
            return "<have not gathered {} yet>".format(i+1)
        h = history[i]
        if not h:
            return "<skipped {}>".format(i+1)
        if isinstance(h, ReturnResult):
            if h.code != 0:
                return "<failed {}>".format(i+1)

            return re.sub(r'\n+$', '', h.out)

        return str(h)

    return re.sub(r'\[R(\d+)\]', subst, cmd)

def expand_glob(cmd):
    r = glob.glob(cmd)
    if len(r) == 0:
        return [cmd]

    return r

def disp_out(msg, indent, out=sys.stdout):
    print(indent+"   " + msg,  end='', file=out)

def disp_err(msg, indent):
    disp_out(add_formatting(msg, codes=[91]), indent, out=sys.stderr)

def ch_dir(path, indent='   ', quiet=False):
    try:
        os.chdir(path)
        pwd = os.getcwd()
        os.environ['PWD'] = pwd
        if not quiet:
            t = add_formatting('Directory;', codes=[1])
            disp_out("{} {}\n".format(t, pwd), indent=indent)
        return True
    except FileNotFoundError:
        disp_err("Directory: {0} does not exist\n". format(path), indent=indent)
    except NotADirectoryError:
        disp_err("{0} is not a directory\n". format(path), indent=indent)
    except PermissionError:
        disp_err("You do not have permissions to change {0}\n". format(path), indent=indent)

    return False

class ReturnResult:
    def __init__(self, out, err, code):
        self.out = out
        self.err = err
        self.code = code

    def __str__(self):
        return "<ReturnResult {}/{}/ec: {}>".format(self.out, self.err, self.code)


class Command:
    def __init__(self, comment=None):
        self._comment = comment
        self._base_colour = 2 

    def process(self, history=None):
        return ""

    def parse(text):
        return None

    def size(self):
        return 1

    def colour(self, colour):
        self._base_colour = colour;

    def accumulate(self, indent='', history=[], stack=[]):
        r, c = self.run(indent=indent, history=history, stack=stack)
        if not c:
            return False
        history.append(r)
        return True

    def activate(self, indent='', history=[], stack=[]):
        name = add_formatting(self.process(history), codes=[90+self._base_colour,1])
        p = prompt.ChoicePrompt(options=['Yes', 'No', 'Quit'], prompt=indent + "Run {}".format(name))
        p.colour(self._base_colour)
        answer = p.get()
        if answer is 'Quit':
            return False

        if answer is "Yes":
            if not self.accumulate(indent=indent, history=history, stack=stack):
                return False
        else:
            history += [None]*self.size()

        return True

class Recipe:
    def __init__(self):
        self._commands = []
        self._base_colour = 2

    def add(self, command):
        self._commands.append(command)
        command.colour(self._base_colour)

    def colour(self, colour):
        self._base_colour = colour
        [c.colour(colour) for c in self._commands]

    def activate(self):
        history = []
        stack = []
        for c in self._commands:
            if not c.activate(history=history, indent=' ', stack=stack):
                return False

        return True

    def parse(self, text, base=Command):
        lines = text.split("\n")
        lines = [l.strip() for l in lines]
        lines = [l for l in lines if len(l) > 0]
        for l in lines: 
            c = base.parse(l)
            if c:
                self._commands.append(c)

    def absorb(self, base=Command):
        r, w, x = select.select([sys.stdin], [], [], 0)
        if r:
            self.parse(r[0].read(), base)
        else:
            for a in sys.argv[1:]:
                self.parse(a, base)
       

class CDCommand(Command):
    def __init__(self, directory, content=None):
        Command.__init__(self, content)
        self._directory = directory

    def process(self, history=None):
        return "Change Directory to: {}".format(self._directory)

    def run(self, indent='', history=[], stack=[]):
        c = False
        if ch_dir(self._directory, indent=indent):
            history.append(self._directory)
            c = True
        else:
            history.append(None)

        return history[-1], c 


class PushDirCommand(CDCommand):
    def __init__(self, directory, content=None):
        CDCommand.__init__(self, directory, content)
                
    def run(self, indent='', history=[], stack=[]):
        stack.append(os.getcwd())
        return CDCommand.run(self, indent=indent, history=history)        


class PopDirCommand(Command):
    def __init__(self, content=None):
        Command.__init__(self, content)
        
    def process(self, history=None):
        return "Return to previous directory"       

    def run(self, indent='', history=[], stack=[]):
        ch_dir(stack.pop(), indent=indent)
        return history[-1], True


class MenuCommand(Command):
    def __init__(self, menu, content=None, default=None):
        Command.__init__(self, content)
        self._menu = menu
        self._default = default

    def process(self, history=None):
        return self._menu.prompt()

    def parse(text):
        ops = text.split('/')
        if len(ops) == 0:
            return None 

        n = ops[0] + "Prompt"
        args = {}
        for o in ops[1:]:
            a = o.split('=', 1)
            args[a[0]] = a[1]

        cmd = None
        try:
            c = getattr(prompt, n)
            m = c(**args)
            cmd = MenuCommand(c(**args))
        except:
            cmd = None

        return cmd;
 
    def run(self, indent='', history=[], stack=[]):
        menu = self._menu
        value = None 
        if isinstance(self._default, str):
            value = replace_history(self._default, history)
        elif self._default:
            value = self._default(history)
        menu.default(value)
        return ReturnResult(",".join(menu.get()), None, 0), True


class ShellCommand(Command):
    def __init__(self, cmd, content=None):
        Command.__init__(self, content)
        self._cmd = cmd if isinstance(cmd, list) else shlex.split(cmd)

    def prepare(self, history, expand=False):
        cmds = []
        for c in [replace_history(c, history) for c in self._cmd]:
            cmds += expand_glob(c) if expand else [c]

        return cmds


    def process(self, history):
        return " ".join(self.prepare(history, expand=False))

    def run(self, indent='', history=[], stack=[]):
        cmd = self.prepare(history, expand=True)
        out = ""
        err = None
        code = 0
        try:
            blocks = [[]]
            for c in cmd:
                if c == '|':
                    blocks.append([])
                else:
                    blocks[-1].append(c)

            fds = []
            read_in = open('/dev/tty', 'r')
            p = subprocess.Popen(blocks[0],
                                 stdin=read_in,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
            fds_out = [p.stdout.fileno()]
            fds_err = [p.stderr.fileno()]
            procs = [p]

            for b in blocks[1:]:
                p = subprocess.Popen(b,
                                     stdin=procs[-1].stdout,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     universal_newlines=True)

                fds_out.remove(procs[-1].stdout.fileno())
                procs.append(p)
                fds_out.append(p.stdout.fileno())
                fds_err.append(p.stderr.fileno())

            def readfds(fds):
                while True:
                    fdsin, _, _ = select.select(fds, [], [])
                    for fd in fdsin:
                        s = ''
                        while True:
                            c = os.read(fd, 1)
                            if len(c) == 0:
                                break
                            try:
                                s += c.decode('utf-8')
                            except Exception as e:
                                s += "<U>"

                            if ord("\n") in c:
                                break;

                        if len(s) == 0:
                            fds.remove(fd)
                            continue
                        yield fd, s

                    if len(fds) == 0:
                        break

            for (fd, s) in readfds(fds_out + fds_err):
                if fd in fds_out:
                    disp_out(s, indent)
                    out += s
                else:
                    disp_err(s, indent)
                    if not err:
                        err = ''
                    err += s

            [p.wait() for p in procs]
            #print([p.returncode for p in procs])
            code = max([p.returncode for p in procs])
                
        except FileNotFoundError as e:
            code, err = e.args
            disp_err(err + "\n", indent)

        if code != 0:
            disp_out(add_formatting('-- Exit Code --: {}\n'.format(code), codes=[91,1]), indent)

        return ReturnResult(out, err, code), True

    def parse(text):
        if len(text) == 0:
            return None

        cmds = text.split()
        if len(cmds) == 2:
            if cmds[0] == 'cd':
                return CDCommand(cmds[1])

            if cmds[0] == 'pushd':
                return PushDirCommand(cmds[1])

        if len(cmds) == 1:
            if cmds[0] == 'popd':
                return PopDirCommand()

        return ShellCommand(text)


class GroupCommand(Command):
    def __init__(self, label, group):
        Command.__init__(self)
        self._label = label
        self._group = []
        for g in group:
            self.add(g)

    def size(self):
        return len(self._group)

    def colour(self, colour):
        Command.colour(self, colour)
        [c.colour(colour) for c in self._group]

    def accumulate(self, indent='', history=[], stack=[]):
        r, c = self.run(history=history, indent=indent, stack=stack)
        return c

    def add(self, cmd):
        if isinstance(cmd, Command):
            self._group.append(cmd)
        elif isinstance(cmd, list):
            self._group.append(ShellCommand(cmd))
        elif isinstance(cmd, str):
            self._group.append(ShellCommand(cmd))
        elif isinstance(cmd, prompt.Base):
            self._group.append(MenuCommand(cmd))
        else:
            print("not supported")

        if len(self._group):
            self._group[-1].colour(self._base_colour)

    def process(self, history=[]):
        return self._label

    def start(self):
        return

    def end(self, history):
        return

    def parse(text, base=None):
        base = base if base else GroupCommand

        m = re.match('^\[(.+?)\]', text)
        if not m:
            return ShellCommand.parse(text)

        label = m.group(1)
        pattern = re.compile(r'''((?:[^;"']|"[^"]*"|'[^']*')+)''')
        group = []
        for c in pattern.split(text[m.span()[1]:])[1::2]:
            group.append(base.parse(c))

        return base(label, group)
    
    def run(self, indent='', history=[], stack=[]):
        pwd = os.getcwd()
        s = stack.copy()
        self.start()
        for c in self._group:
            if not c.activate(history=history, indent=indent+'  ', stack=s):
                return None, False

        self.end(history)
        ch_dir(pwd, quiet=True)
        return None, True
