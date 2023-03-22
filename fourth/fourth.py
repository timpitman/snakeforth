from enum import Enum
from itertools import islice
import collections


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
        self.stack = []  # deque()
        self.state = State.RUN
        self.functions = {}
        self.immediates = {}
        self.function_definition = []
        self.string_definition = None
        self.commenting = False
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
        self.string_definition = None
        self.commenting = False
        for w in words:
            if w == '[':
                self.state = State.RUN
            elif w == ']':
                self.state = State.DEF
            elif w == '(':
                self.commenting = True
            elif self.commenting:
                if w.endswith(')'):
                    self.commenting = False
            elif w == '\\':
                # drop comment
                return
            else:
                if self.state == State.RUN:
                    if self.string_definition is not None:
                        if w.endswith('"'):
                            self.string_definition += w[:-1]
                            print(self.string_definition)
                            self.string_definition = None  # break out of string definition
                        else:
                            self.string_definition += w + " "
                    else:
                        self.eval_word(w, words)
                elif self.state == State.DEF:
                    if function_name is None:
                        function_name = w
                    elif w == ';':
                        if function_name in self.functions:
                            print("redefining function", function_name)
                        self.functions[function_name] = self.function_definition.copy()
                        function_name = None
                        self.state = State.RUN
                    elif w == 'if':
                        self.function_definition.append('0branch')
                        self.stack.append(len(self.function_definition))
                        self.function_definition.append(0)
                    elif w == 'then':
                        update_pos = self.stack.pop()
                        jump = len(self.function_definition) - update_pos - 1
                        self.function_definition[update_pos] = jump
                    elif w == 'else':
                        update_pos = self.stack.pop()
                        self.function_definition.append('branch')
                        self.stack.append(len(self.function_definition))
                        self.function_definition.append(0)
                        # fix original if
                        jump = len(self.function_definition) - update_pos - 1
                        self.function_definition[update_pos] = jump
                    elif w == 'begin':
                        self.stack.append(len(self.function_definition))
                    elif w == 'until':
                        self.function_definition.append('0branch')
                        jump = self.stack.pop() - len(self.function_definition) - 1
                        print("jump:", jump)
                        self.function_definition.append(jump)

                    else:
                        print("appending word to function def:", w)
                        self.function_definition.append(w)

    def eval_word(self, w, words):
        fn = self.functions.get(w, None)
        print("evaluating word:", w)
        if fn is not None:
            if callable(fn):
                fn()
            else:
                self.run(iter(fn))
        elif w.isnumeric():
            self.stack.append(number(w))
        elif w == ':':
            self.state = State.DEF
        elif w == '."':
            self.string_definition = ""
        elif w == "0branch":
            target = next(words)
            if self.stack.pop() == 0:
                consume(words, target)
        elif w == "branch":
            target = next(words)
            consume(words, target)
        else:
            print("?", w)
        # stack.print()

    def parse(self, data):
        words = iter(data.split())
        self.run(words)
        print(list(self.stack))


def number(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


if __name__ == "__main__":
    repl()
