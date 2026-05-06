from __future__ import annotations
from typing import Iterator
from schemas import Token, TokenLexeme, TOKENS, CritterParseError, SET_MULOPS, SET_ADDOPS, T_NONE
from schemas import SET_FACTOR_INITIATOR
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
            obj = self.parseTerm()
            program.addObj(obj)
            token = self.peek()

        parseTree = AbstractSyntaxTree(program)
        return parseTree
    
    def parseExpression(self) -> Expression:
        expression = Expression(self.parseTerm())
        

        return expression
    
    def parseTerm(self) -> Term|BinaryOperator:
        term = Term(self.parseFactor())
        token = self.peek()
        while token.tokenType in SET_MULOPS:
            op = self.getToken()
            binOp = BinaryOperator()
            binOp.setLeft(term)
            binOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            binOp.setRight(Term(self.parseFactor()))
            term = binOp
            token = self.peek()
        return term
    
    def parseMemNode(self) -> MemNode:
        token = self.peek()
        if token.tokenType is not TOKENS.T_MEM:
            raise CritterParseError(f'Error: Expected "mem" but saw "{token.lexeme}".')
        
        token = self.getToken()
        
        token = self.peek()
        if token.tokenType is not TOKENS.T_L_BRACKET:
            raise CritterParseError(f'Error: Expected "[" but saw "{token.lexeme}".')
        token = self.getToken()
        expression = self.parseExpression()
        token = self.peek()
        if token.tokenType is not TOKENS.T_R_BRACKET:
            raise CritterParseError(f'Error: Expected "]" but saw "{token.lexeme}".')
        token = self.getToken()
        return MemNode(expression)

    def parseFactor(self) -> Factor:
        token = self.peek()

        match token.tokenType:
            case TOKENS.T_MEM:
                memNode = self.parseMemNode()
                return Factor(memNode)
            case TOKENS.T_NUMBER:
                number = self.parseNumber()
                return Factor(number)
            case _:
                raise CritterParseError(f'Error: Expected FACTOR but saw "{token.lexeme}".')
    
    def checkFactor(self) -> bool:
        token = self.peek()
        if token.tokenType not in SET_FACTOR_INITIATOR:
            return False
        return True
    
    def parseNumber(self) -> Number:
        if not (token := self.checkNumber()):
            raise CritterParseError(f'Error at line: {self.peek().line} column: {self.peek().column} - Expected <Number> but saw {self.peek().lexeme}')
            
        return Number(token)
    
    def checkNumber(self) -> Token|None:
        token = self.peek()
        if token.tokenType is not TOKENS.T_NUMBER:
            return None
        return self.getToken()
    
            




    


