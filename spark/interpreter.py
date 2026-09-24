"""
Spark Interpreter
------------------
A tree-walking interpreter: walks the AST produced by the Parser and
actually executes it (computes values, runs branches, prints output).
"""

from lexer import Lexer
from parser import Parser
from nodes import (
    NumberLiteral, StringLiteral, BooleanLiteral, ArrayLiteral, IndexExpr,
    Identifier, BinaryOp, UnaryOp, Call,
    LetStmt, AssignStmt, PrintStmt, IfStmt, WhileStmt,
    FuncDef, ReturnStmt, ExprStmt,
)


class SparkRuntimeError(Exception):
    pass


class ReturnSignal(Exception):
    """Used internally to unwind the call stack when 'return' runs."""
    def __init__(self, value):
        self.value = value


class Environment:
    """Holds variables for one scope, with a link to its parent scope."""

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def define(self, name, value):
        self.vars[name] = value

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise SparkRuntimeError(f"Undefined variable '{name}'")

    def assign(self, name, value):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value)
            return
        raise SparkRuntimeError(f"Cannot assign to undefined variable '{name}'")


class SparkFunction:
    """A user-defined Spark function, remembering the scope it was created in."""

    def __init__(self, decl: FuncDef, closure: Environment):
        self.decl = decl
        self.closure = closure

    def call(self, interpreter, args):
        env = Environment(parent=self.closure)
        for param, arg in zip(self.decl.params, args):
            env.define(param, arg)
        try:
            interpreter.execute_block(self.decl.body, env)
        except ReturnSignal as r:
            return r.value
        return None


class Interpreter:
    def __init__(self):
        self.globals = Environment()

    def run(self, statements):
        self.execute_block(statements, self.globals)

    def execute_block(self, statements, env):
        for stmt in statements:
            self._execute(stmt, env)

    def _execute(self, stmt, env):
        if isinstance(stmt, LetStmt):
            value = self._evaluate(stmt.value, env)
            env.define(stmt.name, value)
            return

        if isinstance(stmt, AssignStmt):
            value = self._evaluate(stmt.value, env)
            env.assign(stmt.name, value)
            return

        if isinstance(stmt, PrintStmt):
            value = self._evaluate(stmt.value, env)
            print(self._stringify(value))
            return

        if isinstance(stmt, IfStmt):
            condition = self._evaluate(stmt.condition, env)
            if self._is_truthy(condition):
                self.execute_block(stmt.then_branch, Environment(parent=env))
            elif stmt.else_branch is not None:
                self.execute_block(stmt.else_branch, Environment(parent=env))
            return

        if isinstance(stmt, WhileStmt):
            while self._is_truthy(self._evaluate(stmt.condition, env)):
                self.execute_block(stmt.body, Environment(parent=env))
            return

        if isinstance(stmt, FuncDef):
            func = SparkFunction(stmt, env)
            env.define(stmt.name, func)
            return

        if isinstance(stmt, ReturnStmt):
            value = None
            if stmt.value is not None:
                value = self._evaluate(stmt.value, env)
            raise ReturnSignal(value)

        if isinstance(stmt, ExprStmt):
            self._evaluate(stmt.expr, env)
            return

        raise SparkRuntimeError(f"Unknown statement type: {stmt}")

    # -- expression evaluation --------------------------------------

    def _evaluate(self, expr, env):
        if isinstance(expr, NumberLiteral):
            return expr.value

        if isinstance(expr, StringLiteral):
            return expr.value

        if isinstance(expr, BooleanLiteral):
            return expr.value

        if isinstance(expr, ArrayLiteral):
            return [self._evaluate(el, env) for el in expr.elements]

        if isinstance(expr, IndexExpr):
            array = self._evaluate(expr.array, env)
            index = self._evaluate(expr.index, env)
            if not isinstance(array, list):
                raise SparkRuntimeError("Cannot index a non-array value")
            try:
                return array[int(index)]
            except IndexError:
                raise SparkRuntimeError(f"Array index out of range: {index}")

        if isinstance(expr, Identifier):
            return env.get(expr.name)

        if isinstance(expr, UnaryOp):
            operand = self._evaluate(expr.operand, env)
            if expr.op == "-":
                return -operand
            raise SparkRuntimeError(f"Unknown unary operator '{expr.op}'")

        if isinstance(expr, BinaryOp):
            if expr.op == "and":
                left = self._evaluate(expr.left, env)
                if not self._is_truthy(left):
                    return False
                return self._is_truthy(self._evaluate(expr.right, env))
            if expr.op == "or":
                left = self._evaluate(expr.left, env)
                if self._is_truthy(left):
                    return True
                return self._is_truthy(self._evaluate(expr.right, env))

            left = self._evaluate(expr.left, env)
            right = self._evaluate(expr.right, env)
            return self._apply_binary(expr.op, left, right)

        if isinstance(expr, Call):
            return self._call(expr, env)

        raise SparkRuntimeError(f"Unknown expression type: {expr}")

    def _apply_binary(self, op, left, right):
        if op == "+":
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            if isinstance(left, str) or isinstance(right, str):
                return self._stringify(left) + self._stringify(right)
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        raise SparkRuntimeError(f"Unknown operator '{op}'")

    def _call(self, expr: Call, env):
        args = [self._evaluate(arg, env) for arg in expr.args]

        if expr.callee == "len":
            if len(args) != 1 or not isinstance(args[0], (list, str)):
                raise SparkRuntimeError("len() expects a single array or string argument")
            return len(args[0])

        if expr.callee == "int":
            if len(args) != 1:
                raise SparkRuntimeError("int() expects a single argument")
            return float(int(args[0]))

        callee = env.get(expr.callee)
        if not isinstance(callee, SparkFunction):
            raise SparkRuntimeError(f"'{expr.callee}' is not a function")
        return callee.call(self, args)

    # -- helpers -------------------------------------------------------

    def _is_truthy(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True

    def _stringify(self, value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        if isinstance(value, list):
            return "[" + ", ".join(self._stringify(v) for v in value) + "]"
        return str(value)


def run_source(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    Interpreter().run(ast)


if __name__ == "__main__":
    src = '''
    let nums = [1, 2, 3, 4, 5]
    print(nums)
    print(nums[2])
    print(len(nums))

    let a = true
    let b = false
    if a and b {
        print("both true")
    } else {
        if a or b {
            print("at least one true")
        }
    }
    '''
    run_source(src)