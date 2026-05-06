from __future__ import annotations
from typing import Iterator
from schemas import Token, TokenLexeme, TOKENS, CritterParseError, SET_MULOPS, SET_ADDOPS, T_NONE
from schemas import SET_FACTOR_INITIATOR
from abstractSyntaxTree import AbstractSyntaxTree, Program, MemNode, Expression, BinaryOperator, UnaryOperator, Term, Factor, Number

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
    
    def parseMemNode(self, token: Token|None = None) -> MemNode:
        token = self.peek()
        if token.tokenType is not TOKENS.T_MEM:
            raise CritterParseError(f'Error at line: {token.line} column: {token.column} - Expected "mem" but saw "{token.lexeme}".')
        token = self.getToken()
        token = self.getToken()
        if token.tokenType is not TOKENS.T_L_BRACKET:
            raise CritterParseError(f'Error at line: {token.line} column: {token.column} - Expected "[]" but saw "{token.lexeme}".')
        expression = self.parseExpression()
        token = self.getToken()
        if token.tokenType is not TOKENS.T_R_BRACKET:
            raise CritterParseError(f'Error at line: {token.line} column: {token.column} - Expected "]" but saw "{token.lexeme}".')
        return MemNode(expression)
    

    def parseFactor(self, token: Token|None = None) -> Factor:
        token = self.peek()

        match token.tokenType:
            case TOKENS.T_MEM:
                memNode = self.parseMemNode()
                return Factor(memNode)
            case TOKENS.T_MINUS:
                op = self.getToken()
                unOp = UnaryOperator()
                unOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
                unOp.setOperand(self.parseFactor())
                return Factor(unOp)
            case TOKENS.T_L_PAREN:
                pass
            case TOKENS.T_NUMBER:
                number = self.parseNumber()
                return Factor(number)
            case _:
                raise CritterParseError(f'Error at line: {token.line} column: {token.column} - Expected <Number> but saw {token.lexeme}')
    
    
    def parseNumber(self) -> Number:
        token = self.getToken()
        if token.tokenType is not TOKENS.T_NUMBER:
            raise CritterParseError(f'Error at line: {token.line} column: {token.column} - Expected <Number> but saw {token.lexeme}') 
        return Number(token)
    
    
            




    


