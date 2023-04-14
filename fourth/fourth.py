from enum import Enum
from itertools import islice
import collections

program_fact = """
: factorial
  dup 1 >
  if
    dup 1 -
    factorial *
  else
    drop 1
  then
;
"""

program_fact_loop = """
: factorial
   DUP 2 < IF DROP 1 EXIT THEN 
   DUP 
   BEGIN DUP 2 > WHILE 
   1- SWAP OVER * SWAP 
   REPEAT DROP 
;
"""


def repl(interpreter):
    i = 0
    while True:
        try:
            data: str = input(f"[{i}]: ")
            interpreter.parse(data)
        except EOFError:  # handling ctrl + D
            print()
        except KeyboardInterrupt:  # handling ctrl + C
            print("bye")
            break
        finally:
            i += 1


State = Enum("State", ['RUN', 'DEF'])


def consume(iterator, n):
    """Advance the iterator n-steps ahead. If n is none, consume entirely."""
    # Use functions that consume iterators at C speed.
    if n is None:
        # feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen=0)
    else:
        # advance to the empty slice starting at position n
        next(islice(iterator, n, n), None)


class FourthInterpreter:
    def __init__(self):
        self.stack = []
        self.loop_control_stack = []
        self.state = State.RUN
        self.words = {}
        self.immediates = {}
        self.function_definition = []
        # define our built-in stack functions
        # maths
        self.define_word("+", lambda x, y: (x + y,))
        self.define_word("-", lambda x, y: (x - y,))
        self.define_word("*", lambda x, y: (x * y,))
        self.define_word("/", lambda x, y: (x / y,))
        self.define_word("mod", lambda x, y: (x % y,))
        self.define_word("abs", lambda x: (abs(x),))
        self.define_word("negate", lambda x: (-x,))
        self.define_word("min", lambda x, y: (min(x, y),))
        self.define_word("max", lambda x, y: (max(x, y),))
        self.define_word("2*", lambda x: (x >> 1,))
        self.define_word("2/", lambda x: (x << 1,))
        self.define_word("1+", lambda x: (x + 1,))
        self.define_word("1-", lambda x: (x - 1,))
        # stack manipulation
        self.define_word("dup", lambda x: (x, x))
        self.define_word("drop", lambda x: None)
        self.define_word("swap", lambda x, y: (y, x))
        self.define_word("rot", lambda x, y, z: (y, z, x))
        self.define_word("over", lambda x, y: (x, y, x))
        # comparison
        self.define_word("=", lambda x, y: (-1 if x == y else 0,))
        self.define_word("<", lambda x, y: (-1 if x < y else 0,))
        self.define_word(">", lambda x, y: (-1 if x > y else 0,))
        # bitwise
        self.define_word("and", lambda x, y: (x & y,))
        self.define_word("or", lambda x, y: (x | y,))
        self.define_word("invert", lambda x: (~x,))
        # io
        self.define_word(".", lambda x: print(x, end=''))
        self.define_word("emit", lambda x: print(chr(x), end=''))
        self.define_word("cr", lambda: print())

    def define_word(self, name, function):
        def stack_func():
            num_args = function.__code__.co_argcount
            if len(self.stack) < num_args:
                raise IndexError
            self.stack, args = self.stack[:-num_args], self.stack[-num_args:]
            self.stack.extend(function(*args) or tuple())

        self.words[name] = stack_func

    def run(self, tokens):
        ip = 0

        def next_token():
            nonlocal ip
            nt = tokens[ip]
            ip += 1
            return nt

        while ip < len(tokens):
            t = next_token()
            if t == '[':
                self.state = State.RUN
            elif t == ']':
                self.state = State.DEF
            elif t == '(':
                print("found comment")
                # start of comment - need to find the end
                try:
                    ip = tokens.index(')', ip) + 1
                except ValueError:
                    raise ValueError("'(' is missing the closing ')' to end the comment")
            elif t == ':':
                name = next_token()
                end_index = tokens.index(';', ip)
                word_tokens = tokens[ip:end_index]
                self.words[name.lower()] = word_tokens
                ip = end_index + 1
            elif t == '."':
                # inline string print
                string_definition = ""
                t2 = t
                while not t2.endswith('"'):
                    t2 = next_token()
                    string_definition += t2 + " "
                string_definition += t2[:-1]
                print(string_definition)
            else:
                fn = self.words.get(t, None)
                print("evaluating word:", t)
                if fn is not None:
                    if callable(fn):
                        try:
                            fn()
                        except IndexError:
                            print("End of stack calling function:", t)
                            print("Stack=", self.stack)
                    else:
                        self.run(fn)
                elif t.isnumeric():
                    self.stack.append(number(t))
                elif t == 'if':
                    then_ip = tokens.index('then', ip)
                    # see if we have an else in the middle
                    try:
                        else_ip = tokens.index('else', ip, then_ip)
                    except ValueError:
                        # if statement without else
                        else_ip = -1

                    if else_ip == -1:
                        if self.stack.pop() != 0:
                            self.run(tokens[ip:then_ip])
                    else:
                        if self.stack.pop() != 0:
                            self.run(tokens[ip:else_ip])
                        else:
                            self.run(tokens[else_ip + 1:then_ip])
                    ip = then_ip + 1
                elif t == 'do':
                    end_index = tokens.index('loop', ip)
                    limit = self.stack.pop()
                    index = self.stack.pop()
                    while index < limit:
                        self.run(tokens[ip:end_index])
                        index += 1
                    ip = end_index + 1
                elif t == 'begin':
                    while_index = tokens.index('while', ip)
                    repeat_index = tokens.index('repeat', while_index + 1)
                    while True:
                        self.run(tokens[ip:while_index])
                        if self.stack.pop() == 0:
                            break
                        self.run(tokens[while_index + 1:repeat_index])
                    ip = repeat_index + 1
                elif t == 'recurse':
                    self.run(tokens)
                elif t == 'exit':
                    return
                else:
                    print("unknown word: ", t)

    def parse(self, data):
        # create a list of lowercase tokens, stripping any line comments
        tokens = []
        lines = data.splitlines()
        for line in lines:
            line_tokens = line.lower().split()
            # strip out line comments
            if '//' in line_tokens:
                line_tokens = line_tokens[:line_tokens.index('//')]
            tokens += line_tokens
        self.run(tokens)
        print(self.stack)


def number(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


if __name__ == "__main__":
    interpreter = FourthInterpreter()
    interpreter.parse(program_fact_loop)
    repl(interpreter)
