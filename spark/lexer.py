"""
Spark Lexer
-----------
Turns raw source code (a string) into a flat list of Tokens.

Example:
    "x = 5 + 3"
    -> [IDENT(x), ASSIGN(=), NUMBER(5), PLUS(+), NUMBER(3), EOF]
"""

from dataclasses import dataclass


# ---- Token types -----------------------------------------------------

KEYWORDS = {
    "let": "LET",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "func": "FUNC",
    "return": "RETURN",
    "true": "TRUE",
    "false": "FALSE",
    "print": "PRINT",
    "and": "AND",
    "or": "OR",
}


@dataclass
class Token:
    type: str
    value: object
    line: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.tokens = []

    def _peek(self, offset=0):
        i = self.pos + offset
        if i >= len(self.source):
            return None
        return self.source[i]

    def _advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def _match(self, expected):
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def _add(self, type_, value):
        self.tokens.append(Token(type_, value, self.line))

    def tokenize(self):
        while self.pos < len(self.source):
            ch = self._peek()

            if ch in " \t\r\n":
                self._advance()
                continue

            if ch == "#":
                while self._peek() is not None and self._peek() != "\n":
                    self._advance()
                continue

            if ch.isdigit():
                self._number()
                continue

            if ch.isalpha() or ch == "_":
                self._identifier()
                continue

            if ch == '"':
                self._string()
                continue

            self._symbol()

        self._add("EOF", None)
        return self.tokens

    def _number(self):
        start = self.pos
        while self._peek() is not None and self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1) is not None and self._peek(1).isdigit():
            self._advance()
            while self._peek() is not None and self._peek().isdigit():
                self._advance()
            text = self.source[start:self.pos]
            self._add("NUMBER", float(text))
        else:
            text = self.source[start:self.pos]
            self._add("NUMBER", int(text))

    def _identifier(self):
        start = self.pos
        while self._peek() is not None and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        text = self.source[start:self.pos]
        if text in KEYWORDS:
            self._add(KEYWORDS[text], text)
        else:
            self._add("IDENT", text)

    def _string(self):
        self._advance()
        start = self.pos
        while self._peek() is not None and self._peek() != '"':
            self._advance()
        if self._peek() is None:
            raise LexerError(f"Unterminated string at line {self.line}")
        text = self.source[start:self.pos]
        self._advance()
        self._add("STRING", text)

    def _symbol(self):
        ch = self._advance()

        two_char = {
            ("=", "="): "EQ",
            ("!", "="): "NEQ",
            (">", "="): "GTE",
            ("<", "="): "LTE",
        }

        if (ch, self._peek()) in two_char:
            second = self._advance()
            self._add(two_char[(ch, second)], ch + second)
            return

        single_char = {
            "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH",
            "=": "ASSIGN", ">": "GT", "<": "LT",
            "(": "LPAREN", ")": "RPAREN",
            "{": "LBRACE", "}": "RBRACE",
            "[": "LBRACKET", "]": "RBRACKET",
            ",": "COMMA", ";": "SEMICOLON",
        }

        if ch in single_char:
            self._add(single_char[ch], ch)
            return

        raise LexerError(f"Unexpected character {ch!r} at line {self.line}")


if __name__ == "__main__":
    src = '''
    let x = 5 + 3
    if x > 3 {
        print("big")
    }
    '''
    for tok in Lexer(src).tokenize():
        print(tok)