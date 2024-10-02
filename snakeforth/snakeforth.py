from enum import Enum, auto
from typing import Callable
from inspect import signature
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEMO_PROGRAM = """
\\ calculate factorial using a while loop
: factorial
   DUP 2 < IF DROP 1 EXIT THEN 
   DUP 
   BEGIN DUP 2 > WHILE 
   1- SWAP OVER * SWAP
   REPEAT DROP 
;
4 factorial .
"""


def repl(interpreter):
    """
    a simple repl environment to use the interpreter from the terminal
    """
    i = 0
    while True:
        # print()
        try:
            data: str = input(f"\n({i}): ")
            interpreter.parse(data)
        except EOFError:  # handling ctrl + D
            # pass
            print("???")
        except KeyboardInterrupt:  # handling ctrl + C
            print("bye")
            break
        finally:
            i += 1


class State(Enum):
    """model the interpreter state - running or defining"""

    RUN = auto()  # running
    DEF = auto()  # defining


class ForthInterpreter:
    def __init__(self):
        self.stack = []
        self.control_stack = []
        self.loop_stack = []
        self.words = {}
        self.variables = []
        self.state = State.RUN
        self.function_name = None
        self.function_definition = []

        self.define_builtins()

    def define_builtins(self):
        """define our built-in stack functions"""
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
        self.define_word(".", lambda x: print(x, end=""))
        self.define_word("emit", lambda x: print(chr(x), end=""))
        self.define_word("cr", lambda: print())
        # misc
        self.define_word("true", lambda: (-1,))
        self.define_word("false", lambda: (0,))
        # variable access
        self.define_word("!", lambda x, y: self.variable_store(x, y))
        self.define_word("@", lambda x: (self.variable_fetch(x),))
        # debugging
        self.define_word(".s", lambda: self.print_stack())

    def variable_store(self, x, y):
        self.variables[y] = x

    def variable_fetch(self, x):
        return self.variables[x]

    def run_current_block(self):
        return (
            self.control_stack and self.control_stack[-1][1]
        ) or not self.control_stack

    def run_parent_block(self):
        if len(self.control_stack) >= 2:
            return self.control_stack[-2][1]
        else:
            return True

    def define_word(self, name: str, function: Callable) -> None:
        def stack_func():
            # determine the number of arguments from the function's Signature
            num_args = len(signature(function).parameters)
            if len(self.stack) < num_args:
                raise IndexError(f"word {name} called without sufficient stack")
            if num_args > 0:
                # take arguments from the stack
                args = self.stack[-num_args:]
                self.stack = self.stack[:-num_args]
            else:
                args = []
            self.stack.extend(function(*args) or tuple())

        self.words[name] = stack_func

    def print_stack(self):
        # .S command to debug the stack by printing it
        stack_contents = " ".join(map(str, self.stack))
        print(f"<{len(self.stack)}> {stack_contents}")

    def run(self, tokens: list[str]) -> None:
        self.state = State.RUN
        self.function_name = None
        self.function_definition = []
        ip = 0  # instruction pointer indexes the next token

        def next_token():
            """helper to pull the next token"""
            nonlocal ip
            nt = tokens[ip]
            ip += 1
            return nt

        while ip < len(tokens):
            t = next_token()
            if t == "(":
                # start of comment - need to find the end
                try:
                    ip = tokens.index(")", ip) + 1
                except ValueError:
                    raise SyntaxError(
                        "'(' is missing the closing ')' to end the comment"
                    )
            elif t == ":":
                # starting a function definition
                self.function_name = next_token().lower()
                self.state = State.DEF
            elif t == ";":
                # ending a function definition
                if self.function_name in self.words:
                    logger.debug("redefining function: %s", self.function_name)
                self.words[self.function_name] = self.function_definition.copy()
                self.function_name = None
                # back to running
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
                # search words for this token
                fn = self.words.get(t, None)
                logger.debug("evaluating word: %s", t)
                if fn is not None:
                    if callable(fn):
                        try:
                            fn()
                        except IndexError:
                            logger.error("End of stack calling function: %s", t)
                            logger.error("Stack: %s", self.stack)
                    elif isinstance(fn, int):
                        # variable address or const to put on stack
                        self.stack.append(fn)
                    else:
                        self.run(fn)
                elif t == "0branch":
                    target = int(next_token())
                    if self.stack.pop() == 0:
                        ip += target
                elif t == "branch":
                    target = int(next_token())
                    ip += target
                elif t == "recurse":
                    self.run(tokens)
                elif t == "exit":
                    return
                elif t == "variable":
                    name = next_token().lower()
                    if name in self.words:
                        logger.error("variable name already taken: %s", name)
                    else:
                        variable_address = len(self.variables)
                        self.variables.append(0)
                        self.words[name] = variable_address
                elif t == "constant":
                    name = next_token().lower()
                    if name in self.words:
                        logger.error("constant name already taken: %s", name)
                    else:
                        self.words[name] = self.stack.pop()
                else:
                    # try to convert to an int or float
                    try:
                        num = int(t)
                        self.stack.append(num)
                    except ValueError:
                        try:
                            num = float(t)
                            self.stack.append(num)
                        except ValueError:
                            logger.error("unknown word: %s", t)

            elif self.state == State.DEF:
                # we're inside a function definition
                if t == "if":
                    self.function_definition.append("0branch")
                    self.stack.append(len(self.function_definition))
                    self.function_definition.append(0)
                elif t == "then":
                    update_pos = self.stack.pop()
                    jump = len(self.function_definition) - update_pos - 1
                    self.function_definition[update_pos] = jump
                    logger.debug("then updating prev jump=%d", jump)
                elif t == "else":
                    update_pos = self.stack.pop()
                    self.function_definition.append("branch")
                    self.stack.append(len(self.function_definition))
                    self.function_definition.append(0)
                    # fix original if
                    jump = len(self.function_definition) - update_pos - 1
                    self.function_definition[update_pos] = jump
                    logger.debug("else updating if jump=%d", jump)
                elif t == "begin":
                    self.stack.append(len(self.function_definition))
                elif t == "until":
                    self.function_definition.append("0branch")
                    jump = self.stack.pop() - len(self.function_definition) - 1
                    logger.debug("jump: %d", jump)
                    self.function_definition.append(jump)
                elif t == "while":
                    dest = self.stack.pop()
                    self.function_definition.append("0branch")
                    self.stack.append(len(self.function_definition))
                    self.function_definition.append(0)
                    self.stack.append(dest)
                elif t == "repeat":
                    self.function_definition.append("branch")
                    jump = self.stack.pop() - len(self.function_definition) - 1
                    logger.debug("jump: %d", jump)
                    self.function_definition.append(jump)
                    update_pos = self.stack.pop()
                    jump = len(self.function_definition) - update_pos - 1
                    self.function_definition[update_pos] = jump
                    logger.debug("then updating prev while=%d", jump)
                elif t == "again":
                    self.function_definition.append("branch")
                    jump = self.stack.pop() - len(self.function_definition) - 1
                    self.function_definition.append(jump)
                else:
                    logger.debug("appending word to function def: %s", t)
                    self.function_definition.append(t)
            logger.debug(self.stack)

    def parse(self, data: str) -> None:
        # create a list of lowercase tokens, stripping any line comments
        tokens = []
        lines = data.splitlines()
        for line in lines:
            line_tokens = line.lower().split()
            # strip out line comments
            if "\\" in line_tokens:
                line_tokens = line_tokens[: line_tokens.index("\\")]
            tokens += line_tokens
        # run the resulting tokens
        self.run(tokens)
        logger.debug(self.stack)


if __name__ == "__main__":
    print("SnakeForth forth interpreter")
    # create our interpreter and parse the demo program
    interp = ForthInterpreter()
    interp.parse(DEMO_PROGRAM)
    # start the repl
    repl(interp)
