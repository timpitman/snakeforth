# SnakeForth Documentation

## Introduction

SnakeForth is a simple Forth interpreter implemented in Python. This project serves as both a learning tool for those interested in the Forth programming language and as a practical demonstration of implementing an interpreter for a stack-based language in Python.

SnakeForth was created as an exercise to learn Forth, motivated by an interest in the minimalism of the Forth programming language and its use in bootstrapping embedded systems.

## What is Forth?

Forth is a stack-based, procedural, and extensible programming language created in the late 1960s by Charles H. Moore. It features:

- A simple syntax based on space-separated "words" (commands)
- A dual-stack architecture (data stack and return stack)
- Postfix notation (operations follow their operands)
- The ability to define new words from existing ones
- Direct memory access capabilities
- Minimal syntax and compact code

Forth's minimalism and extensibility have made it popular in embedded systems, firmware, and bootstrapping applications where resources are limited.

## Features of SnakeForth

SnakeForth implements a subset of the Forth language, focusing on core functionality:

- **Stack Manipulation**: Basic stack operations (DUP, DROP, SWAP, OVER, etc.)
- **Arithmetic Operations**: Basic math functions (+, -, *, /, MOD)
- **Comparison Operators**: Equality and relational tests (=, <, >, etc.)
- **Control Structures**: Conditional execution (IF, ELSE, THEN) and loops (BEGIN, UNTIL, DO, LOOP)
- **Word Definition**: The ability to define new words using `:` and `;`
- **Variables and Constants**: Creating and accessing named values
- **Comment Support**: Using `(` and `)` or `\` for comments
- **Interactive Mode**: A REPL (Read-Eval-Print Loop) for interactive use

## Getting Started

### Prerequisites

- Python 3.6 or higher

### Installation

```bash
# Clone the repository
git clone https://github.com/timpitman/snakeforth.git
cd snakeforth

# No additional dependencies required - pure Python!
```

### Basic Usage

```bash
# Run the interpreter in interactive mode
python snakeforth.py

# Run a Forth script
python snakeforth.py example.fs
```

## Examples

### Basic Stack Operations

```forth
5 3 + .     \ Output: 8
10 2 * 4 /  \ Puts 5 on the stack
DUP         \ Duplicates the top item, stack now has 5 5
*           \ Multiplies, stack now has 25
.           \ Outputs: 25
```

### Defining New Words

```forth
: SQUARED DUP * ;  \ Define a word that squares a number
5 SQUARED .        \ Output: 25

: CUBE DUP SQUARED * ;  \ Define a word using another defined word
3 CUBE .                \ Output: 27
```

### Conditional Execution

```forth
: ABS DUP 0 < IF NEGATE THEN ;  \ Absolute value function
-5 ABS .                         \ Output: 5
```

### Simple Loop

```forth
: COUNTDOWN BEGIN DUP . 1- DUP 0 = UNTIL DROP ;
5 COUNTDOWN  \ Outputs: 5 4 3 2 1
```

## Code Structure

The SnakeForth interpreter is organized around these core components:

- **Tokenizer**: Breaks input text into Forth tokens
- **Parser**: Interprets tokens according to Forth syntax
- **Stack**: Manages the data stack operations
- **Dictionary**: Stores built-in and user-defined words
- **Interpreter**: Coordinates the parsing and execution process

## Extending SnakeForth

You can extend SnakeForth by:

1. Adding new built-in words in Python
2. Creating libraries of useful Forth words in separate files
3. Implementing advanced Forth features like the return stack or memory access

## Implementation Details

SnakeForth follows a straightforward implementation approach:

1. Tokenize input by splitting on whitespace
2. Process tokens one by one:
   - Numbers are pushed to the stack
   - Words are looked up in the dictionary and executed
3. Handle special forms like word definitions and control structures
4. Provide appropriate error handling and stack inspection

## Advanced Topics

### Creating Custom Words

The heart of Forth's power lies in defining new words. In SnakeForth, you can create increasingly complex functionality by building on simpler words:

```forth
: TRIPLE 3 * ;
: SQUARED DUP * ;
: CUBED DUP SQUARED * ;
: 4TH-POWER SQUARED SQUARED ;
```

### Error Handling

SnakeForth provides informative error messages for common issues:

- Stack underflow (not enough items on stack)
- Unknown word references
- Incomplete control structures
- Invalid numeric input

## Contributing

Contributions to SnakeForth are welcome! Please feel free to submit pull requests or open issues on GitHub.
