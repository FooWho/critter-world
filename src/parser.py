from __future__ import annotations
from typing import Iterator
from schemas import Token, TokenLexeme, TOKENS, CritterParseError, SET_MULOPS, SET_ADDOPS, T_NONE
from abstractSyntaxTree import AbstractSyntaxTree, Program, MemNode, Expression, BinaryOperator, Term, Factor, Number

class Parser():

    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens = tokens
        self.current = next(self.tokens, Token(TOKENS.T_NONE, '', 0, 0))

    def getToken(self) -> Token:
        token = self.current
        self.current = next(self.tokens, Token(TOKENS.T_NONE, '', 0, 0))
        return token
    
    def peek(self) -> Token:
        return self.current
    
    def parse(self) -> AbstractSyntaxTree:
        program = Program()

        token = self.peek()
        while token.tokenType is not TOKENS.T_EOF:
            term = self.parseTerm()
            program.addTermOrFactorOrBinary(term)
            token = self.peek()

        parseTree = AbstractSyntaxTree(program)
        return parseTree
    
    def parseExpression(self) -> Expression:
        return Expression()
    
    def parseTerm(self) -> Term|BinaryOperator:
        term = Term(self.parseFactor())
        while self.peek().tokenType in SET_ADDOPS:
            op = self.getToken()
            binOp = BinaryOperator()
            binOp.setLeft(term)
            binOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            binOp.setRight(Term(self.parseFactor()))
            term = binOp
        return term

    def parseFactor(self) -> Factor:
        token = self.peek()
        if token.tokenType is TOKENS.T_MEM:
            token = self.getToken()
            token = self.peek()
            if token.tokenType is TOKENS.T_L_BRACKET:
                expression = self.parseExpression()
                token = self.peek()
                if token.tokenType is TOKENS.T_R_BRACKET:
                    token = self.getToken()
                    memNode = MemNode(expression)
                    return Factor(memNode)
                else:
                    raise CritterParseError(f'Error: Expected "]" but saw "{token.lexeme}".')
            else:
                raise CritterParseError(f'Error: Expected "[" but saw "{token.lexeme}".')
        else:
            pass
            

        return Factor()
    
    def parseNumber(self) -> Number:
        if self.peek().tokenType is TOKENS.T_NUMBER:
            token = self.getToken()
            return Number(TokenLexeme(token.tokenType, token.lexeme))
        else:
            raise CritterParseError(f'Error: Expected <Number> but saw {self.peek().lexeme}')

"""
    def parseFactor(self) -> Factor|BinaryOperator:
        factor = Factor(self.parseNumber())
        while self.peek().tokenType in SET_MULOPS:
            op = self.getToken()
            binOp = BinaryOperator()
            binOp.setLeft(factor)
            binOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            binOp.setRight(Factor(self.parseNumber()))
            factor = binOp
        return factor
"""



    


