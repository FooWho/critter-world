from __future__ import annotations
from typing import Iterator
from schemas import Token, TokenLexeme, TOKENS, CritterParseError, SET_MULOPS, SET_ADDOPS
from schemas import SET_SUGAR, SET_SENSORS, SET_RELOPS
from abstractSyntaxTree import (AbstractSyntaxTree, Program, MemNode, SensorNode, Expression, LogicalOperator, 
                                RelationalOperator, BinaryOperator, UnaryOperator, Term, Factor, Number, Condition)


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
            obj = self.parseCondition()
            program.addObj(obj)
            token = self.peek()

        parseTree = AbstractSyntaxTree(program)
        return parseTree
    
    def parseCondition(self) -> Condition:
        conjunction = self.parseConjunction()

        token = self.peek()
        while token.tokenType is TOKENS.T_OR:
            op = self.getToken()
            logOp = LogicalOperator()
            logOp.setLeft(conjunction)
            logOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            logOp.setRight(self.parseConjunction())
            conjunction = logOp
            token = self.peek()

        return Condition(conjunction)


    def parseConjunction(self) -> RelationalOperator|LogicalOperator|Condition:
        relation = self.parseRelation()

        token = self.peek()
        while token.tokenType is TOKENS.T_AND:
            op = self.getToken()
            logOp = LogicalOperator()
            logOp.setLeft(relation)
            logOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            logOp.setRight(self.parseRelation())
            relation = logOp
            token = self.peek()    
        return relation

    def parseExpression(self) -> Expression:
        expression = Expression(self.parseTerm())
        token = self.peek()
        while token.tokenType in SET_ADDOPS:
            op = self.getToken()
            binOp = BinaryOperator()
            binOp.setLeft(expression.expression)
            binOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            binOp.setRight(self.parseTerm())
            expression.expression = binOp
            token = self.peek()       
        return expression
    
    def parseRelation(self) -> RelationalOperator|Condition:
        token = self.peek()
        if token.tokenType is TOKENS.T_L_BRACE:
            self.getToken()
            condition = self.parseCondition()
            brace = self.getToken()
            if brace.tokenType is not TOKENS.T_R_BRACE:
                raise CritterParseError(brace, '}')
            condition.setBrace(True)
            return condition
            
        leftExpr = self.parseExpression()
        token = self.peek()
        if token.tokenType not in SET_RELOPS:
            raise CritterParseError(token, '<SET_RELOPS>')
        op = self.getToken()
        relOp = RelationalOperator()
        relOp.setLeft(leftExpr)
        relOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
        relOp.setRight(self.parseExpression())
        return relOp
                          
    
    def parseTerm(self) -> Term|BinaryOperator:
        term = Term(self.parseFactor())
        token = self.peek()
        while token.tokenType in SET_MULOPS:
            op = self.getToken()
            binOp = BinaryOperator()
            binOp.setLeft(term)
            binOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            binOp.setRight(self.parseFactor())
            term = binOp
            token = self.peek()
        return term
    

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
    
    def parseSensor(self) -> SensorNode:
        token = self.peek()
        match token.tokenType:
            case TOKENS.T_AHEAD | TOKENS.T_NEARBY | TOKENS.T_RANDOM:
                token = self.getToken()
                sensorType = token
                token = self.getToken()
                if token.tokenType is not TOKENS.T_L_BRACKET:
                    raise CritterParseError(token, '[')
                expression = self.parseExpression()
                token = self.getToken()
                if token.tokenType is not TOKENS.T_R_BRACKET:
                    raise CritterParseError(token, ']')
                sensorNode = SensorNode(sensorType, expression)
            case TOKENS.T_SMELL:
                token = self.getToken()
                sensorType = token
                sensorNode = SensorNode(sensorType)
            case _:
                raise CritterParseError(token, '<SENSOR>')
        return sensorNode


    def parseFactor(self) -> Factor:
        token = self.peek()
        match token.tokenType:
            case TOKENS.T_MEM:
                memNode = self.parseMemNode()
                return Factor(memNode)
            case sugar if sugar in SET_SUGAR:
                token = self.getToken()
                memNode = MemNode.desugar(token)
                return Factor(memNode)
            case sensor if sensor.name in [sensor.name for sensor in SET_SENSORS]: 
                sensor = self.parseSensor()
                return Factor(sensor)
            case TOKENS.T_MINUS:
                op = self.getToken()
                unOp = UnaryOperator()
                unOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
                unOp.setOperand(self.parseFactor())
                return Factor(unOp)
            case TOKENS.T_L_PAREN:
                paren = self.getToken()
                inner = self.parseExpression()
                paren = self.getToken()
                if paren.tokenType is not TOKENS.T_R_PAREN:
                    raise CritterParseError(paren, ')')
                return Factor(inner)
            case TOKENS.T_NUMBER:
                number = self.parseNumber()
                return Factor(number)
            case _:
                raise CritterParseError(token, '<Factor>')
    
    
    def parseNumber(self) -> Number:
        token = self.getToken()
        if token.tokenType is not TOKENS.T_NUMBER:
            raise CritterParseError(token, '<Number>') 
        return Number(token)
    
    
            




    
