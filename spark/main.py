"""
Spark CLI
---------
Entry point: reads a .spark source file and runs it.

Usage:
    python3 main.py path/to/program.spark
"""

import sys

from lexer import Lexer, LexerError
from parser import Parser, ParseError
from interpreter import Interpreter, SparkRuntimeError


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <file.spark>")
        sys.exit(1)

    path = sys.argv[1]

    try:
        with open(path, "r") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        sys.exit(1)

    try:
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        Interpreter().run(ast)
    except LexerError as e:
        print(f"Lexer error: {e}")
        sys.exit(1)
    except ParseError as e:
        print(f"Parse error: {e}")
        sys.exit(1)
    except SparkRuntimeError as e:
        print(f"Runtime error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()