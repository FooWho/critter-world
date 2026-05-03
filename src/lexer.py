import re
from typing import Iterator, TYPE_CHECKING
from enum import StrEnum
from schemas import Token, TokenLexeme, CritterParseError, TOKENS


class Lexer():
    
    def __init__(self) -> None:
        self.combinedPattern = '|'.join([f'(?P<{member.name}>{member.value})' for member in TOKENS])
        self.compiledPattern = re.compile(self.combinedPattern)

    def tokenize(self, code: str) -> Iterator[Token]:
        tokenType: TOKENS
        lexeme: str 
        lineNumber:int
        column: int
        lineStart: int
        tmp: str|None

        lineStart = 0
        lineNumber = 0
        for tc in self.compiledPattern.finditer(code):
            tmp = tc.lastgroup

            if tmp:
                tokenType = TOKENS[tmp]
            else:
                tokenType = TOKENS.T_MISMATCH

            lexeme = tc.group()
            column = tc.start() - lineStart

            if tokenType == TOKENS.T_WS:
                if '\n' in lexeme:
                    lineNumber += lexeme.count('\n')
                    lineStart = tc.end()
                continue
            elif tokenType == TOKENS.T_COMMENT:
                lineNumber += lexeme.count('\n')
                lineStart = tc.end()
            elif tokenType == TOKENS.T_MISMATCH:
                raise CritterParseError(f'Error parsing critter program. Read: "{lexeme}" at line {lineNumber} column {column}.')
            yield Token(tokenType, lexeme, lineNumber, column)


    def emitTokens(self, loc: str) -> list[str|None]:
        return [match.lastgroup for match in self.compiledPattern.finditer(loc)]
    
    def emitLexemes(self, loc: str) -> list[str]:
        return [match.group() for match in self.compiledPattern.finditer(loc)]
    
    def emitLexemeTokenPair(self, loc: str) -> list[TokenLexeme]:
        return [TokenLexeme(token.tokenType, token.lexeme) for token in self.tokenize(loc)]
    

