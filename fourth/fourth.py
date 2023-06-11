from enum import Enum


program_fft = """
\ Complex arithmetic words
: c+ ( r1 i1 r2 i2 -- r3 i3 )
  rot + swap rot + swap ;

: c* ( r1 i1 r2 i2 -- r3 i3 )
  over over * swap over * swap
  rot over * - swap
  rot over * + ;

: cswap ( r1 i1 r2 i2 -- r2 i2 r1 i1 )
  rot swap rot swap ;

\ Bit reversal
: bit-reverse ( n bit_length -- n_reversed )
  0 swap 0
  do
    over 1 and if
      swap 1 + swap
    else
      2drop 1
    then
    swap 2/ swap 1 +
  loop
  swap drop ;

: fft ( n -- )
  \ Bit-reversal reordering
  1
  2dup 1 - 0
  do
    2dup i bit-reverse =
    if
      2drop
    else
      4 * i 4 * cswap
    then
    1 +
  loop

  \ FFT
  1
  2dup
  do
    1
    i 2 / 0
    do
      0
      2dup
      do
        2dup j 4 * 2dup i 4 * +
        2dup i 2/ 2mod 1 and 0= if
          1e0 0e0
        else
          2 * pi i 2/ / fsin fcos
        then
        c* c+
        2dup 2 / 2mod i 4 * + cswap
        2dup i 4 * + cswap
        4 +
      +loop
      2drop
    loop
    2 *
  loop
  2drop ;
"""


def repl(interpreter):
    i = 0
    while True:
        try:
            data: str = input(f"({i}): ")
            interpreter.parse(data)
        except EOFError:  # handling ctrl + D
            print()
        except KeyboardInterrupt:  # handling ctrl + C
            print("bye")
            break
        finally:
            i += 1


State = Enum("State", ['RUN', 'DEF'])


class FourthInterpreter:
    def __init__(self):
        self.stack = []
        self.control_stack = []
        self.loop_stack = []
        self.words = {}
        self.variables = []
        self.state = State.RUN
        self.function_name = None
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
        self.define_word("2dup", lambda x, y: (x, y, x, y))
        self.define_word("drop", lambda x: None)
        self.define_word("2drop", lambda x, y: None)
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
        self.define_word("xor", lambda x, y: (x ^ y,))
        self.define_word("invert", lambda x: (~x,))
        self.define_word("lshift", lambda x, y: (x << y,))
        self.define_word("rshift", lambda x, y: (x >> y,))
        # io
        self.define_word(".", lambda x: print(x, end=''))
        self.define_word("emit", lambda x: print(chr(x), end=''))
        self.define_word("cr", lambda: print())
        # control flow
        self.define_word("if", lambda x: self._if(x))
        self.define_word("else", lambda: self._else())
        self.define_word("then", lambda: self._then())
        # misc
        self.define_word("true", lambda: (-1,))
        self.define_word("false", lambda: (0,))
        # variable access
        self.define_word("!", lambda x, y: self.variable_store(x, y))
        self.define_word("@", lambda x: (self.variable_fetch(x),))

    def variable_store(self, x, y):
        self.variables[y] = x

    def variable_fetch(self, x):
        return self.variables[x]

    def run_current_block(self):
        return (self.control_stack and self.control_stack[-1][1]) or not self.control_stack

    def run_parent_block(self):
        if len(self.control_stack) >= 2:
            return self.control_stack[-2][1]
        else:
            return True

    def define_word(self, name, function):
        def stack_func():
            num_args = function.__code__.co_argcount
            if len(self.stack) < num_args:
                raise IndexError(f"word {name} called without sufficient stack")
            if num_args > 0:
                self.stack, args = self.stack[:-num_args], self.stack[-num_args:]
            else:
                args = []
            self.stack.extend(function(*args) or tuple())

        self.words[name] = stack_func

    def run(self, tokens):
        self.state = State.RUN
        self.function_name = None
        self.function_definition = []
        ip = 0

        def next_token():
            nonlocal ip
            nt = tokens[ip]
            ip += 1
            return nt

        while ip < len(tokens):
            t = next_token()
            if t == '(':
                print("found comment")
                # start of comment - need to find the end
                try:
                    ip = tokens.index(')', ip) + 1
                except ValueError:
                    raise SyntaxError("'(' is missing the closing ')' to end the comment")
            elif t == ':':
                self.function_name = next_token().lower()
                self.state = State.DEF
            elif t == ';':
                if self.function_name in self.words:
                    print("redefining function", self.function_name)
                self.words[self.function_name] = self.function_definition.copy()
                self.function_name = None
                self.state = State.RUN
            elif self.state == State.RUN:
                if t == '."':
                    # inline string print
                    string_definition = ""
                    t2 = t
                    while not t2.endswith('"'):
                        t2 = next_token()
                        string_definition += t2 + " "
                    string_definition += t2[:-1]
                    print(string_definition)
                fn = self.words.get(t, None)
                print("evaluating word:", t)
                if fn is not None:
                    if callable(fn):
                        try:
                            fn()
                        except IndexError:
                            print("End of stack calling function:", t)
                            print("Stack=", self.stack)
                    elif isinstance(fn, int):
                        # variable address or const to put on stack
                        self.stack.append(fn)
                    else:
                        self.run(fn)
                elif t == "0branch":
                    target = next_token()
                    if self.stack.pop() == 0:
                        ip += target
                elif t == "branch":
                    target = next_token()
                    ip += target
                elif t == 'recurse':
                    self.run(tokens)
                elif t == 'exit':
                    return
                elif t == 'variable':
                    name = next_token().lower()
                    if name in self.words:
                        print("variable name already taken:", name)
                    else:
                        variable_address = len(self.variables)
                        self.variables.append(0)
                        self.words[name] = variable_address
                elif t == 'constant':
                    name = next_token().lower()
                    if name in self.words:
                        print("constant name already taken:", name)
                    else:
                        self.words[name] = self.stack.pop()
                else:
                    # try to convert to an int
                    try:
                        num = int(t)
                        self.stack.append(num)
                    except ValueError:
                        print("unknown word: ", t)

            elif self.state == State.DEF:
                if t == 'if':
                    self.function_definition.append('0branch')
                    self.stack.append(len(self.function_definition))
                    self.function_definition.append(0)
                elif t == 'then':
                    update_pos = self.stack.pop()
                    jump = len(self.function_definition) - update_pos - 1
                    self.function_definition[update_pos] = jump
                    print("then updating prev jump=", jump)
                elif t == 'else':
                    update_pos = self.stack.pop()
                    self.function_definition.append('branch')
                    self.stack.append(len(self.function_definition))
                    self.function_definition.append(0)
                    # fix original if
                    jump = len(self.function_definition) - update_pos - 1
                    self.function_definition[update_pos] = jump
                    print("else updating if jump=", jump)
                elif t == 'begin':
                    self.stack.append(len(self.function_definition))
                elif t == 'until':
                    self.function_definition.append('0branch')
                    jump = self.stack.pop() - len(self.function_definition) - 1
                    print("jump:", jump)
                    self.function_definition.append(jump)
                elif t == 'while':
                    dest = self.stack.pop()
                    self.function_definition.append('0branch')
                    self.stack.append(len(self.function_definition))
                    self.function_definition.append(0)
                    self.stack.append(dest)
                elif t == 'repeat':
                    self.function_definition.append('branch')
                    jump = self.stack.pop() - len(self.function_definition) - 1
                    print("jump:", jump)
                    self.function_definition.append(jump)
                    update_pos = self.stack.pop()
                    jump = len(self.function_definition) - update_pos - 1
                    self.function_definition[update_pos] = jump
                    print("then updating prev while=", jump)
                elif t == 'again':
                    self.function_definition.append('branch')
                    jump = self.stack.pop() - len(self.function_definition) - 1
                    self.function_definition.append(jump)
                else:
                    print("appending word to function def:", t)
                    self.function_definition.append(t)
            print(self.stack)

    def parse(self, data):
        # create a list of lowercase tokens, stripping any line comments
        tokens = []
        lines = data.splitlines()
        for line in lines:
            line_tokens = line.lower().split()
            # strip out line comments
            if '\\' in line_tokens:
                line_tokens = line_tokens[:line_tokens.index('\\')]
            tokens += line_tokens
        self.run(tokens)
        print(self.stack)


if __name__ == "__main__":
    interpreter = FourthInterpreter()
    interpreter.parse(program_fft)
    #interpreter.parse("1e0 0e0 2e0 0e0 3e0 0e0 4e0 0e0 4 fft")
    interpreter.parse("1 0 2 0 3 0 4 0 4 fft")
    repl(interpreter)
