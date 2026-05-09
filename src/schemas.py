from __future__ import annotations
from enum import StrEnum
from typing import NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from abstractSyntaxTree import Term, Factor, Number

class TOKENS(StrEnum):
    T_MEMSIZE = r'\bMEMSIZE\b' 
    T_DEFENSE = r'\bDEFENSE\b'
    T_OFFENSE = r'\bOFFENSE\b'
    T_SIZE = r'\bSIZE\b'
    T_ENERGY = r'\bENERGY\b'
    T_PASS = r'\bPASS'
    T_POSTURE = r'\bPOSTURE\b'
    T_COMMENT = r'//.*'
    T_COMM = r'-->'
    T_ASSIGN = r':='
    T_LEQU = r'<='
    T_GEQU = r'>='
    T_NEQU = r'!='
    T_MEM = r'\bmem\b'
    T_WAIT = r'\bwait\b'
    T_FORWARD = r'\bforward\b'
    T_BACKWARD = r'\bbackward\b'
    T_LEFT = r'\bleft\b'
    T_RIGHT = r'\bright\b'
    T_EAT = r'\beat\b'
    T_ATTACK = r'\battack\b'
    T_GROW = r'\bgrow\b'
    T_BUD = r'\bbud\b'
    T_SERVE = r'\bserve\b'
    T_NEARBY = r'\bnearby\b'
    T_AHEAD = r'\bahead\b'
    T_RANDOM = r'\brandom\b'
    T_SMELL = r'\bsmell\b'
    T_AND = r'\band\b'
    T_OR = r'\bor\b'
    T_MOD = r'\bmod\b'
    T_STAR = r'\*'
    T_DIV = r'/'
    T_PLUS = r'\+'
    T_MINUS = r'\-'
    T_LESS = r'<'
    T_GREAT = r'>'
    T_EQU = r'='
    T_L_PAREN = r'\('
    T_R_PAREN = r'\)'
    T_L_BRACKET = r'\['
    T_R_BRACKET = r'\]'
    T_L_BRACE = r'\{'
    T_R_BRACE = r'\}'
    T_SEMICOLON = r';'
    T_NUMBER = r'\d+'
    T_WS = r'\s'
    T_EOF = r'\Z'
    T_MISMATCH = r'.*'
    T_NONE = r''

class Token(NamedTuple):
    tokenType: TOKENS
    lexeme: str
    line: int
    column: int

class TokenLexeme(NamedTuple):
    tokenType: TOKENS
    lexeme: str

class CritterParseError(Exception):
    def __init__(self, token: Token, expected: str) -> None:
        self.message = f'Error at line: {token.line} column: {token.column} - Expected "{expected}" but saw <{token.tokenType.name}>:"{token.lexeme}".'
        super().__init__(self.message)

SET_RELOPS = {TOKENS.T_LESS, TOKENS.T_LEQU, TOKENS.T_EQU, TOKENS.T_NEQU, TOKENS.T_GREAT, TOKENS.T_GEQU}
SET_ADDOPS = {TOKENS.T_PLUS, TOKENS.T_MINUS}
SET_MULOPS = {TOKENS.T_STAR, TOKENS.T_DIV, TOKENS.T_MOD}
SET_SENSORS = {TOKENS.T_NEARBY, TOKENS.T_AHEAD, TOKENS.T_RANDOM, TOKENS.T_SMELL}

SET_SUGAR = {TOKENS.T_MEMSIZE, TOKENS.T_DEFENSE, TOKENS.T_OFFENSE, TOKENS.T_SIZE, TOKENS.T_ENERGY, TOKENS.T_PASS, TOKENS.T_POSTURE}

T_NONE = TokenLexeme(TOKENS.T_NONE, '')
