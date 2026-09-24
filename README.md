# Spark

Spark is a small, custom-built programming language, implemented from
scratch in Python. It includes a **lexer**, a **recursive-descent parser**,
and a **tree-walking interpreter** — the full pipeline that turns source
text into a running program.

```
let x = 10
let y = 20

if x + y > 25 {
    print("big total")
} else {
    print("small total")
}

func multiply(a, b) {
    return a * b
}

print(multiply(4, 5))
```

## Features

- Variables (`let`)
- Arithmetic (`+ - * /`) and comparison (`== != > < >= <=`) operators
- Logical operators (`and`, `or`)
- `if` / `else` conditionals
- `while` loops
- Functions with parameters, `return`, and closures
- Arrays and indexing (`[1, 2, 3]`, `arr[0]`)
- Strings, numbers, and booleans
- Comments (`# like this`)

## Architecture

| File              | Responsibility                                            |
|-------------------|-------------------------------------------------------------|
| `lexer.py`        | Turns source text into a flat list of tokens               |
| `nodes.py`        | AST node definitions (data classes)                         |
| `parser.py`       | Recursive-descent parser: tokens -> AST                     |
| `interpreter.py`  | Tree-walking interpreter: AST -> executed program            |
| `main.py`         | CLI entry point: run a `.spark` file                         |

## Usage

```bash
python3 main.py examples/hello.spark
```

## Example programs

See the `examples/` folder for more sample `.spark` programs, including
FizzBuzz and a Fibonacci sequence generator.

## Why I built this

This project was built to understand, from the ground up, how programming
languages actually work — how source code becomes tokens, how tokens
become a syntax tree, and how that tree is executed. It covers the same
core pipeline used by real interpreters and compilers.