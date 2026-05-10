from __future__ import annotations
from typing import Iterator
from schemas import TOKENS, Token, TokenLexeme, CritterParseError, SET_ADDOPS, SET_MULOPS, SET_RELOPS
from abstractSyntaxTree import Program, Number, UnaryOperator, MemNode, BinaryOperator, RelationalOperator

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
    
    def parse(self) -> Program:
        program = Program()

        token = self.peek()
        while token.tokenType is not TOKENS.T_EOF:
            obj = self.parseRelation()
            program.setRoot(obj)
            token = self.peek()

        parseTree = program
        return parseTree

    def parseRelation(self) -> RelationalOperator:
        token = self.peek()
        relOp = RelationalOperator()

        if token.tokenType is TOKENS.T_L_BRACE:
            pass
        else:
            leftOperand = self.parseExpression()
            operatorToken = self.getToken()
            if operatorToken.tokenType not in SET_RELOPS:
                raise CritterParseError(operatorToken, '<RelationalOperator>')
            operator = TokenLexeme(operatorToken.tokenType, operatorToken.lexeme)
            rightOperand = self.parseExpression()
            relOp = RelationalOperator(leftOperand, operator, rightOperand)
        return relOp

    def parseExpression(self) -> Number|MemNode|UnaryOperator|BinaryOperator:
        expression = self.parseTerm()
        token = self.peek()
        while token.tokenType in SET_ADDOPS:
            op = self.getToken()
            binOp = BinaryOperator()
            binOp.setLeftOperand(expression)
            binOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            binOp.setRightOperand(self.parseTerm())
            expression = binOp
            token = self.peek()       
        return expression
    
    def parseTerm(self) -> Number|MemNode|UnaryOperator|BinaryOperator:
        term = self.parseFactor()
        token = self.peek()
        while token.tokenType in SET_MULOPS:
            op = self.getToken()
            binOp = BinaryOperator()
            binOp.setLeftOperand(term)
            binOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            binOp.setRightOperand(self.parseFactor())
            term = binOp
            token = self.peek()
        return term
    
    def parseFactor(self) -> Number|UnaryOperator|MemNode|BinaryOperator:

        token = self.peek()
        match token.tokenType:
            case TOKENS.T_MEM:
                memNode = self.parseMemNode()
                return memNode
            #case sugar if sugar in SET_SUGAR:
            #    token = self.getToken()
            #    memNode = MemNode.desugar(token)
            #    return Factor(memNode)
            #case sensor if sensor.name in [sensor.name for sensor in SET_SENSORS]: 
            #    sensor = self.parseSensor()
            #    return Factor(sensor)
            case TOKENS.T_MINUS:
                op = self.getToken()
                unOp = UnaryOperator()
                unOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
                unOp.setOperand(self.parseFactor())
                return unOp
            case TOKENS.T_L_PAREN:
                paren = self.getToken()
                innerFactor = self.parseExpression()
                paren = self.getToken()
                if paren.tokenType is not TOKENS.T_R_PAREN:
                    raise CritterParseError(paren, ')')
                return innerFactor
            case TOKENS.T_NUMBER:
                number = self.parseNumber()
                return number
            case _:
                raise CritterParseError(token, '<Factor>')
            
    def parseMemNode(self) -> MemNode:
        token = self.peek()
        if token.tokenType is not TOKENS.T_MEM:
            raise CritterParseError(token, 'mem')
        token = self.getToken()
        token = self.getToken()
        if token.tokenType is not TOKENS.T_L_BRACKET:
            raise CritterParseError(token, '[')
        expression = self.parseExpression()
        token = self.getToken()
        if token.tokenType is not TOKENS.T_R_BRACKET:
            raise CritterParseError(token, ']')
        return MemNode(expression)
            
    def parseNumber(self) -> Number:
        token = self.getToken()
        if token.tokenType is not TOKENS.T_NUMBER:
            raise CritterParseError(token, '<Number>') 
        return Number(token)