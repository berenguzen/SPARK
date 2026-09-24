"""
Spark Parser
------------
A recursive-descent parser: turns the flat Token list from the Lexer
into a tree of AST nodes (see nodes.py).

Grammar (roughly, in order of precedence, lowest to highest):

    program    -> statement*
    statement  -> letStmt | assignStmt | ifStmt | whileStmt
                | funcDef | returnStmt | printStmt | exprStmt
    block      -> "{" statement* "}"

    expression -> logical_or
    logical_or -> logical_and ("or" logical_and)*
    logical_and-> equality ("and" equality)*
    equality   -> comparison (("==" | "!=") comparison)*
    comparison -> term ((">" | "<" | ">=" | "<=") term)*
    term       -> factor (("+" | "-") factor)*
    factor     -> unary (("*" | "/") unary)*
    unary      -> "-" unary | postfix
    postfix    -> primary ("[" expression "]")*
    primary    -> NUMBER | STRING | "true" | "false"
                | "[" args "]"                     # array literal
                | IDENT ("(" args ")")?             # variable or function call
                | "(" expression ")"
"""

from lexer import Lexer, Token
from nodes import (
    NumberLiteral, StringLiteral, BooleanLiteral, ArrayLiteral, IndexExpr,
    Identifier, BinaryOp, UnaryOp, Call,
    LetStmt, AssignStmt, PrintStmt, IfStmt, WhileStmt,
    FuncDef, ReturnStmt, ExprStmt,
)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos]

    def _peek_next(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None

    def _advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _check(self, type_):
        return self._peek().type == type_

    def _match(self, *types):
        if self._peek().type in types:
            return self._advance()
        return None

    def _expect(self, type_, message):
        if self._check(type_):
            return self._advance()
        tok = self._peek()
        raise ParseError(f"{message} (got {tok.type} '{tok.value}' at line {tok.line})")

    def parse(self):
        statements = []
        while not self._check("EOF"):
            statements.append(self._statement())
        return statements

    def _block(self):
        self._expect("LBRACE", "Expected '{' to start a block")
        statements = []
        while not self._check("RBRACE") and not self._check("EOF"):
            statements.append(self._statement())
        self._expect("RBRACE", "Expected '}' to close a block")
        return statements

    def _statement(self):
        if self._check("LET"):
            return self._let_stmt()
        if self._check("IF"):
            return self._if_stmt()
        if self._check("WHILE"):
            return self._while_stmt()
        if self._check("FUNC"):
            return self._func_def()
        if self._check("RETURN"):
            return self._return_stmt()
        if self._check("PRINT"):
            return self._print_stmt()
        if self._check("IDENT") and self._peek_next() is not None and self._peek_next().type == "ASSIGN":
            return self._assign_stmt()

        expr = self._expression()
        return ExprStmt(expr)

    def _let_stmt(self):
        self._advance()
        name_tok = self._expect("IDENT", "Expected variable name after 'let'")
        self._expect("ASSIGN", "Expected '=' after variable name")
        value = self._expression()
        return LetStmt(name_tok.value, value)

    def _assign_stmt(self):
        name_tok = self._advance()
        self._expect("ASSIGN", "Expected '=' in assignment")
        value = self._expression()
        return AssignStmt(name_tok.value, value)

    def _print_stmt(self):
        self._advance()
        self._expect("LPAREN", "Expected '(' after 'print'")
        value = self._expression()
        self._expect("RPAREN", "Expected ')' after print argument")
        return PrintStmt(value)

    def _if_stmt(self):
        self._advance()
        condition = self._expression()
        then_branch = self._block()
        else_branch = None
        if self._match("ELSE"):
            else_branch = self._block()
        return IfStmt(condition, then_branch, else_branch)

    def _while_stmt(self):
        self._advance()
        condition = self._expression()
        body = self._block()
        return WhileStmt(condition, body)

    def _func_def(self):
        self._advance()
        name_tok = self._expect("IDENT", "Expected function name after 'func'")
        self._expect("LPAREN", "Expected '(' after function name")
        params = []
        if not self._check("RPAREN"):
            params.append(self._expect("IDENT", "Expected parameter name").value)
            while self._match("COMMA"):
                params.append(self._expect("IDENT", "Expected parameter name").value)
        self._expect("RPAREN", "Expected ')' after parameters")
        body = self._block()
        return FuncDef(name_tok.value, params, body)

    def _return_stmt(self):
        self._advance()
        value = None
        if not self._check("RBRACE") and not self._check("EOF"):
            value = self._expression()
        return ReturnStmt(value)

    # -- expressions (precedence climbing) --------------------------

    def _expression(self):
        return self._logical_or()

    def _logical_or(self):
        expr = self._logical_and()
        while self._check("OR"):
            self._advance()
            right = self._logical_and()
            expr = BinaryOp(expr, "or", right)
        return expr

    def _logical_and(self):
        expr = self._equality()
        while self._check("AND"):
            self._advance()
            right = self._equality()
            expr = BinaryOp(expr, "and", right)
        return expr

    def _equality(self):
        expr = self._comparison()
        while self._check("EQ") or self._check("NEQ"):
            op_tok = self._advance()
            right = self._comparison()
            expr = BinaryOp(expr, op_tok.value, right)
        return expr

    def _comparison(self):
        expr = self._term()
        while self._peek().type in ("GT", "LT", "GTE", "LTE"):
            op_tok = self._advance()
            right = self._term()
            expr = BinaryOp(expr, op_tok.value, right)
        return expr

    def _term(self):
        expr = self._factor()
        while self._peek().type in ("PLUS", "MINUS"):
            op_tok = self._advance()
            right = self._factor()
            expr = BinaryOp(expr, op_tok.value, right)
        return expr

    def _factor(self):
        expr = self._unary()
        while self._peek().type in ("STAR", "SLASH"):
            op_tok = self._advance()
            right = self._unary()
            expr = BinaryOp(expr, op_tok.value, right)
        return expr

    def _unary(self):
        if self._check("MINUS"):
            self._advance()
            operand = self._unary()
            return UnaryOp("-", operand)
        return self._postfix()

    def _postfix(self):
        expr = self._primary()
        while self._check("LBRACKET"):
            self._advance()
            index = self._expression()
            self._expect("RBRACKET", "Expected ']' after index")
            expr = IndexExpr(expr, index)
        return expr

    def _primary(self):
        tok = self._peek()

        if tok.type == "NUMBER":
            self._advance()
            return NumberLiteral(tok.value)

        if tok.type == "STRING":
            self._advance()
            return StringLiteral(tok.value)

        if tok.type == "TRUE":
            self._advance()
            return BooleanLiteral(True)

        if tok.type == "FALSE":
            self._advance()
            return BooleanLiteral(False)

        if tok.type == "LBRACKET":
            return self._array_literal()

        if tok.type == "IDENT":
            self._advance()
            if self._check("LPAREN"):
                return self._finish_call(tok.value)
            return Identifier(tok.value)

        if tok.type == "LPAREN":
            self._advance()
            expr = self._expression()
            self._expect("RPAREN", "Expected ')' after expression")
            return expr

        raise ParseError(f"Unexpected token {tok.type} '{tok.value}' at line {tok.line}")

    def _array_literal(self):
        self._expect("LBRACKET", "Expected '['")
        elements = []
        if not self._check("RBRACKET"):
            elements.append(self._expression())
            while self._match("COMMA"):
                elements.append(self._expression())
        self._expect("RBRACKET", "Expected ']' after array elements")
        return ArrayLiteral(elements)

    def _finish_call(self, name):
        self._expect("LPAREN", "Expected '(' to start call arguments")
        args = []
        if not self._check("RPAREN"):
            args.append(self._expression())
            while self._match("COMMA"):
                args.append(self._expression())
        self._expect("RPAREN", "Expected ')' after arguments")
        return Call(name, args)


if __name__ == "__main__":
    src = '''
    let arr = [1, 2, 3]
    print(arr[1])

    let a = true
    let b = false
    if a and b {
        print("both true")
    } else {
        print("not both true")
    }
    '''
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    for stmt in ast:
        print(stmt)