from __future__ import annotations
from typing import Iterator
from schemas import TOKENS, Token, TokenLexeme, CritterParseError, SET_ADDOPS, SET_MULOPS, SET_RELOPS, SET_SENSORS, SET_SUGAR
from abstractSyntaxTree import Program, Number, UnaryOperator, MemNode, BinaryOperator, RelationalOperator, LogicalOperator, SensorNode, SmellNode, DirectedSensorNode, BooleanOperator, ExpressionNode

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
            obj = self.parseCondition()
            program.setRoot(obj)
            token = self.peek()

        parseTree = program
        return parseTree
    
    def parseCondition(self) -> BooleanOperator:
        conjunction = self.parseConjunction()
        token = self.peek()
        while token.tokenType is TOKENS.T_OR:
            op = self.getToken()
            logOp = LogicalOperator()
            logOp.setLeftOperand(conjunction)
            logOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            logOp.setRightOperand(self.parseConjunction())
            conjunction = logOp
            token = self.peek()       
        return conjunction
    
    def parseConjunction(self) -> BooleanOperator:
        relation = self.parseRelation()
        token = self.peek()
        while token.tokenType is TOKENS.T_AND:
            op = self.getToken()
            logOp = LogicalOperator()
            logOp.setLeftOperand(relation)
            logOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
            logOp.setRightOperand(self.parseRelation())
            relation = logOp
            token = self.peek()
        return relation


    def parseRelation(self) -> BooleanOperator:
        token = self.peek()
        relOp = RelationalOperator()

        if token.tokenType is TOKENS.T_L_BRACE:
            token = self.getToken()
            innerCondition = self.parseCondition()
            token = self.getToken()
            if token.tokenType is not TOKENS.T_R_BRACE:
                raise CritterParseError(token, '}')
            return innerCondition
        else:
            leftOperand = self.parseExpression()
            operatorToken = self.getToken()
            if operatorToken.tokenType not in SET_RELOPS:
                raise CritterParseError(operatorToken, '<RelationalOperator>')
            operator = TokenLexeme(operatorToken.tokenType, operatorToken.lexeme)
            rightOperand = self.parseExpression()
            relOp = RelationalOperator(leftOperand, operator, rightOperand)
        return relOp

    def parseExpression(self) -> ExpressionNode:
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
    
    def parseTerm(self) -> ExpressionNode:
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
    
    def parseFactor(self) -> ExpressionNode:
        token = self.peek()
        match token.tokenType:
            case TOKENS.T_MEM:
                memNode = self.parseMemNode()
                return memNode
            case sugar if sugar in SET_SUGAR:
                token = self.getToken()
                memNode = MemNode.desugar(token)
                return memNode
            case sensor if sensor in SET_SENSORS: 
                sensorNode = self.parseSensor()
                return sensorNode
            case TOKENS.T_MINUS:
                op = self.getToken()
                unOp = UnaryOperator()
                unOp.setOperator(TokenLexeme(op.tokenType, op.lexeme))
                unOp.setOperand(self.parseFactor())
                return unOp
            case TOKENS.T_L_PAREN:
                token = self.getToken()
                innerFactor = self.parseExpression()
                token = self.getToken()
                if token.tokenType is not TOKENS.T_R_PAREN:
                    raise CritterParseError(token, ')')
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
        
    def parseSensor(self) -> SensorNode:
        token = self.peek()
        if token.tokenType not in SET_SENSORS:
            raise CritterParseError(token, '<Sensor>')
        sensorToken = self.getToken()
        
        if sensorToken.tokenType is TOKENS.T_SMELL:
            return SmellNode(sensorToken)
            
        token = self.getToken()
        if token.tokenType is not TOKENS.T_L_BRACKET:
            raise CritterParseError(token, '[')
        
        expression = self.parseExpression()

        token = self.getToken()
        if token.tokenType is not TOKENS.T_R_BRACKET:
            raise CritterParseError(token, ']')
        return DirectedSensorNode(sensorToken, expression)
            
    def parseNumber(self) -> Number:
        token = self.getToken()
        if token.tokenType is not TOKENS.T_NUMBER:
            raise CritterParseError(token, '<Number>') 
        return Number(token)