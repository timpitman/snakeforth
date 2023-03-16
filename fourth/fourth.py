from collections import deque
from itertools import islice
from enum import Enum


def repl():
    interpreter = FourthInterpreter()
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


State = Enum("State", ['RUN', 'DEF', 'STRING'])


class Stack:
    def __init__(self):
        self.stack = []  # deque()
        self.state = State.RUN

    def push(self, data):
        self.stack.append(data)

    def pop(self):
        return self.stack.pop()

    def is_empty(self):
        return len(self.stack) == 0

    def dup(self):
        self.push(self.stack[-1])

    def swap(self):
        self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    def over(self):
        self.push(self.stack[-2])

    def rot(self):
        self.push(self.stack[-3])
        del self.stack[-4]

    def print(self):
        print(list(self.stack))

    def top(self):
        return self.stack[-1]


class FourthInterpreter:
    def __init__(self):
        self.stack = []  # deque()
        self.state = State.RUN
        self.functions = {}
        self.function_definition = []
        self.string_definition = ""

        self.define_word("+", lambda x, y: (x + y,))
        self.define_word("-", lambda x, y: (x - y,))
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
            self.stack, args = self.stack[:-num_args], self.stack[-num_args:]
            self.stack.extend(function(*args) or tuple())

        self.functions[name] = stack_func

    def run(self, words):
        function_name = None
        string = []
        for w in words:
            if self.state == State.RUN:
                self.eval_word(w)
            elif self.state == State.DEF:
                if function_name is None:
                    function_name = w
                elif w == ';':
                    if function_name in self.functions:
                        print("redefining function", function_name)
                    self.functions[function_name] = self.function_definition.copy()
                    function_name = None
                    self.state = State.RUN
                else:
                    self.function_definition.append(w)
            elif self.state == State.STRING:
                if w.endswith('"'):
                    self.string_definition += w[:-1]
                    print(self.string_definition)
                    self.state = State.RUN
                else:
                    self.string_definition += w + " "

    def eval_word(self, w):
        fn = self.functions.get(w, None)
        if fn is not None:
            if callable(fn):
                fn()
            else:
                self.run(fn)
        elif w.isnumeric():
            self.stack.append(number(w))
        elif w == ':':
            self.state = State.DEF
        elif w == '."':
            self.state = State.STRING
            self.string_definition = ""
        else:
            print("?", w)
        # stack.print()

    def parse(self, data):
        words = data.split()
        self.run(words)
        print(list(self.stack))


def number(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


if __name__ == "__main__":
    repl()
