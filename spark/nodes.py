"""
Spark AST Nodes
---------------
Plain data classes representing the syntax tree. The Parser builds these,
and the Interpreter later walks them to actually run the program.
"""

from dataclasses import dataclass, field


# ---- Expressions (things that produce a value) ------------------------

@dataclass
class NumberLiteral:
    value: float


@dataclass
class StringLiteral:
    value: str


@dataclass
class BooleanLiteral:
    value: bool


@dataclass
class ArrayLiteral:
    elements: list = field(default_factory=list)


@dataclass
class IndexExpr:
    array: object
    index: object


@dataclass
class Identifier:
    name: str


@dataclass
class BinaryOp:
    left: object
    op: str      # e.g. "+", "-", "==", ">", "and", "or"
    right: object


@dataclass
class UnaryOp:
    op: str
    operand: object


@dataclass
class Call:
    callee: str
    args: list = field(default_factory=list)


# ---- Statements (things that do something) -----------------------------

@dataclass
class LetStmt:
    name: str
    value: object


@dataclass
class AssignStmt:
    name: str
    value: object


@dataclass
class PrintStmt:
    value: object


@dataclass
class IfStmt:
    condition: object
    then_branch: list
    else_branch: list = None


@dataclass
class WhileStmt:
    condition: object
    body: list


@dataclass
class FuncDef:
    name: str
    params: list
    body: list


@dataclass
class ReturnStmt:
    value: object = None


@dataclass
class ExprStmt:
    expr: object