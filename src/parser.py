from __future__ import annotations
from typing import Iterator
from schemas import (
    TOKENS,
    Token,
    TokenLexeme,
    CritterParseError,
    SET_ADDOPS,
    SET_MULOPS,
    SET_RELOPS,
    SET_SENSORS,
    SET_SUGAR,
    SET_ACTIONS,
)
from abstractSyntaxTree import (
    Program,
    Number,
    UnaryOperator,
    MemNode,
    BinaryOperator,
    RelationalOperator,
    LogicalOperator,
    SensorNode,
    SmellNode,
    DirectedSensorNode,
    BooleanOperator,
    ExpressionNode,
    Command,
    Update,
    Action,
    ServeAction,
    Rule,
)


class Parser:

    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens = tokens
        self.current = next(self.tokens, Token(TOKENS.T_NONE, "", 0, 0))

    def getToken(self) -> Token:
        token = self.current
        self.current = next(self.tokens, Token(TOKENS.T_NONE, "", 0, 0))
        return token

    def peek(self) -> Token:
        return self.current

    def parse(self) -> Program:
        program = Program()

        program.rules.append(self.parseRule())
        token = self.peek()
        while token.tokenType is not TOKENS.T_EOF:
            rule = self.parseRule()
            program.rules.append(rule)
            token = self.peek()

        return program

    def parseRule(self) -> Rule:
        condition = self.parseCondition()
        token = self.getToken()
        if token.tokenType is not TOKENS.T_COMM:
            raise CritterParseError(token, "-->")
        commandBlock = self.parseCommandBlock()
        return Rule(condition, commandBlock)

    def parseCommandBlock(self) -> list[Command]:
        commands: list[Command] = []
        command = self.parseCommand()
        commands.append(command)
        token = self.peek()
        while token.tokenType is not TOKENS.T_SEMICOLON:
            if isinstance(command, Action):
                raise CritterParseError(token, ";")
            command = self.parseCommand()
            commands.append(command)
            token = self.peek()
        token = self.getToken()
        return commands

    def parseCommand(self) -> Command:
        token = self.peek()
        match token.tokenType:
            case toke if toke in SET_SUGAR | {TOKENS.T_MEM}:
                command = self.parseUpdate()
            case toke if toke in SET_ACTIONS:
                command = self.parseAction()
            case _:
                raise CritterParseError(token, '<Update>, <Action>, or ";"')
        return command

    def parseAction(self) -> Command:
        token = self.peek()
        match token.tokenType:
            case TOKENS.T_SERVE:
                action = self.parseServeAction()
            case toke if toke in (SET_ACTIONS - {TOKENS.T_SERVE}):
                token = self.getToken()
                action = Action(token)
            case _:
                raise CritterParseError(token, "<Action>")
        return action

    def parseServeAction(self) -> Command:
        serve_token = self.getToken()
        token = self.getToken()
        if token.tokenType is not TOKENS.T_L_BRACKET:
            raise CritterParseError(token, "[")
        expression = self.parseExpression()
        token = self.getToken()
        if token.tokenType is not TOKENS.T_R_BRACKET:
            raise CritterParseError(token, "]")
        serveAction = ServeAction(serve_token, expression)
        return serveAction

    def parseUpdate(self) -> Command:
        memNode = self.parseMemNode()
        token = self.getToken()
        if token.tokenType is not TOKENS.T_ASSIGN:
            raise CritterParseError(token, ":=")
        expression = self.parseExpression()
        return Update(memNode, expression)

    def parseCondition(self) -> BooleanOperator:
        conjunction = self.parseConjunction()
        token = self.peek()
        while token.tokenType is TOKENS.T_OR:
            op = self.getToken()
            logOp = LogicalOperator()
            logOp.leftOperand = conjunction
            logOp.operator = TokenLexeme(op.tokenType, op.lexeme)
            logOp.rightOperand = self.parseConjunction()
            conjunction = logOp
            token = self.peek()
        return conjunction

    def parseConjunction(self) -> BooleanOperator:
        relation = self.parseRelation()
        token = self.peek()
        while token.tokenType is TOKENS.T_AND:
            op = self.getToken()
            logOp = LogicalOperator()
            logOp.leftOperand = relation
            logOp.operator = TokenLexeme(op.tokenType, op.lexeme)
            logOp.rightOperand = self.parseRelation()
            relation = logOp
            token = self.peek()
        return relation

    def parseRelation(self) -> BooleanOperator:
        token = self.peek()

        if token.tokenType is TOKENS.T_L_BRACE:
            self.getToken()
            innerCondition = self.parseCondition()
            token = self.getToken()
            if token.tokenType is not TOKENS.T_R_BRACE:
                raise CritterParseError(token, "}")
            return innerCondition

        leftOperand = self.parseExpression()
        operatorToken = self.getToken()
        if operatorToken.tokenType not in SET_RELOPS:
            raise CritterParseError(operatorToken, "<RelationalOperator>")
        operator = TokenLexeme(operatorToken.tokenType, operatorToken.lexeme)
        rightOperand = self.parseExpression()
        return RelationalOperator(leftOperand, operator, rightOperand)

    def parseExpression(self) -> ExpressionNode:
        expression = self.parseTerm()
        while self.peek().tokenType in SET_ADDOPS:
            op = self.getToken()
            binOp = BinaryOperator()
            binOp.leftOperand = expression
            binOp.operator = TokenLexeme(op.tokenType, op.lexeme)
            binOp.rightOperand = self.parseTerm()
            expression = binOp
        return expression

    def parseTerm(self) -> ExpressionNode:
        term = self.parseFactor()
        while self.peek().tokenType in SET_MULOPS:
            op = self.getToken()
            binOp = BinaryOperator()
            binOp.leftOperand = term
            binOp.operator = TokenLexeme(op.tokenType, op.lexeme)
            binOp.rightOperand = self.parseFactor()
            term = binOp
        return term

    def parseFactor(self) -> ExpressionNode:
        token = self.peek()
        match token.tokenType:
            case toke if toke in SET_SUGAR | {TOKENS.T_MEM}:
                memNode = self.parseMemNode()
                return memNode
            case sensor if sensor in SET_SENSORS:
                sensorNode = self.parseSensor()
                return sensorNode
            case TOKENS.T_MINUS:
                op = self.getToken()
                unOp = UnaryOperator()
                unOp.operator = TokenLexeme(op.tokenType, op.lexeme)
                unOp.operand = self.parseFactor()
                return unOp
            case TOKENS.T_L_PAREN:
                token = self.getToken()
                innerFactor = self.parseExpression()
                token = self.getToken()
                if token.tokenType is not TOKENS.T_R_PAREN:
                    raise CritterParseError(token, ")")
                return innerFactor
            case TOKENS.T_NUMBER:
                number = self.parseNumber()
                return number
            case _:
                raise CritterParseError(token, "<Factor>")

    def parseMemNode(self) -> MemNode:
        token = self.peek()
        if token.tokenType in SET_SUGAR:
            token = self.getToken()
            return MemNode.desugar(token)

        self.getToken()

        token = self.getToken()
        if token.tokenType is not TOKENS.T_L_BRACKET:
            raise CritterParseError(token, "[")
        expression = self.parseExpression()

        token = self.getToken()
        if token.tokenType is not TOKENS.T_R_BRACKET:
            raise CritterParseError(token, "]")
        return MemNode(expression)

    def parseSensor(self) -> SensorNode:
        token = self.peek()
        if token.tokenType not in SET_SENSORS:
            raise CritterParseError(token, "<Sensor>")
        sensorToken = self.getToken()

        if sensorToken.tokenType is TOKENS.T_SMELL:
            return SmellNode(sensorToken)

        token = self.getToken()
        if token.tokenType is not TOKENS.T_L_BRACKET:
            raise CritterParseError(token, "[")

        expression = self.parseExpression()

        token = self.getToken()
        if token.tokenType is not TOKENS.T_R_BRACKET:
            raise CritterParseError(token, "]")
        return DirectedSensorNode(sensorToken, expression)

    def parseNumber(self) -> Number:
        token = self.getToken()
        if token.tokenType is not TOKENS.T_NUMBER:
            raise CritterParseError(token, "<Number>")
        return Number(token)
