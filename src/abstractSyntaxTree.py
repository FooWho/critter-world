from __future__ import annotations
from typing import Any, ClassVar, Iterator
from schemas import TokenLexeme, TOKENS, Token, SET_MULOPS, SET_ADDOPS, T_NONE

class AbstractSyntaxTree():
    pass
    
class Program(AbstractSyntaxTree):

    def __init__(self, rootNode: LogicalOperator|RelationalOperator|BinaryOperator|UnaryOperator|Number|MemNode|SensorNode|None = None) -> None:
        self.rootNode = rootNode or Number()
    
    def __str__(self) -> str:
        return str(self.rootNode)
    
    def setRoot(self, root: LogicalOperator|RelationalOperator|BinaryOperator|UnaryOperator|Number|MemNode|SensorNode) -> None:
        self.rootNode = root

    def getRoot(self) -> LogicalOperator|RelationalOperator|BinaryOperator|UnaryOperator|Number|MemNode|SensorNode:
        return self.rootNode

class ASTNode():
    _children: ClassVar[tuple[str, ...]] = ()

    def __iter__(self) -> Iterator[ASTNode]:
        for fieldName in self._children:
            value = getattr(self, fieldName, None)
            if isinstance(value, list):
                yield from (item for item in value
                            if isinstance(item, ASTNode))
            elif isinstance(value, ASTNode):
                yield value

class LogicalOperator(ASTNode):
    _children = ('leftOperand', 'operator', 'rightOperand')

    def __init__(self, leftOperand: RelationalOperator|LogicalOperator|None = None, 
                 operator: TokenLexeme = T_NONE, 
                 rightOperand: RelationalOperator|LogicalOperator|None = None) -> None:  
            
        self.leftOperand = leftOperand or RelationalOperator()
        self.operator = operator
        self.rightOperand = rightOperand or RelationalOperator()

    def __str__(self) -> str:
        tmpStr = ''

        if self.breakingPrecedence(self.leftOperand):
            tmpStr += '{' + str(self.leftOperand) + '}'
        else:    
            tmpStr += str(self.leftOperand)

        tmpStr += ' ' + self.operator.lexeme + ' '

        if self.breakingPrecedence(self.rightOperand):
            tmpStr += '{' + str(self.rightOperand) + '}'
        else:
            tmpStr += str(self.rightOperand)

        return  tmpStr

    def setLeftOperand(self, operand: RelationalOperator|LogicalOperator) -> None:
        self.leftOperand = operand

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRightOperand(self, operand: RelationalOperator|LogicalOperator) -> None:
        self.rightOperand = operand

    def evaluate(self) -> bool:
        match self.operator.tokenType:
            case TOKENS.T_AND:
                return self.leftOperand.evaluate() and self.rightOperand.evaluate()
            case TOKENS.T_OR:
                return self.leftOperand.evaluate() or self.rightOperand.evaluate()
            case _:
                raise ValueError(f'Expected <LogicalOperator> in evaluation. Saw: "{self.operator.lexeme}"')
            
    def breakingPrecedence(self, operand: RelationalOperator|LogicalOperator):
        if (isinstance(self.leftOperand, LogicalOperator) and 
            (self.operator.tokenType is TOKENS.T_AND and 
             self.leftOperand.operator.tokenType is TOKENS.T_OR)):
            return True
        return False

class RelationalOperator(ASTNode):
    _children = ('leftOperand', 'operator', 'rightOperand')

    def __init__(self, leftOperand: UnaryOperator|MemNode|Number|BinaryOperator|SensorNode|None = None, 
                 operator: TokenLexeme = T_NONE, 
                 rightOperand: UnaryOperator|MemNode|Number|BinaryOperator|SensorNode|None = None) -> None:      
        self.leftOperand = leftOperand or Number()
        self.operator = operator
        self.rightOperand = rightOperand or Number()

    def __str__(self) -> str:
        return str(self.leftOperand) + ' ' + self.operator.lexeme + ' ' + str(self.rightOperand)

    def setLeftOperand(self, operand: UnaryOperator|MemNode|Number|BinaryOperator|SensorNode) -> None:
        self.leftOperand = operand

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRightOperand(self, operand: UnaryOperator|MemNode|Number|BinaryOperator|SensorNode) -> None:
        self.rightOperand = operand

    def evaluate(self) -> bool:
        match self.operator.tokenType:
            case TOKENS.T_LESS:
                return self.leftOperand.evaluate() < self.rightOperand.evaluate()
            case TOKENS.T_LEQU:
                return self.leftOperand.evaluate() <= self.rightOperand.evaluate()
            case TOKENS.T_EQU:
                return self.leftOperand.evaluate() == self.rightOperand.evaluate()
            case TOKENS.T_GEQU:
                return self.leftOperand.evaluate() >= self.rightOperand.evaluate()
            case TOKENS.T_GREAT:
                return self.leftOperand.evaluate() > self.rightOperand.evaluate()
            case TOKENS.T_NEQU:
                return self.leftOperand.evaluate() != self.rightOperand.evaluate()
            case _:
                raise ValueError(f'Expected <RelationalOperator> in evaluation. Saw: "{self.operator.lexeme}"')


class BinaryOperator(ASTNode):
    _children = ('leftOperand', 'operator', 'rightOperand')

    def __init__(self, leftOperand: UnaryOperator|MemNode|Number|BinaryOperator|SensorNode|None = None, 
                 operator: TokenLexeme = T_NONE, 
                 rightOperand: UnaryOperator|MemNode|Number|BinaryOperator|SensorNode|None = None) -> None:      
        self.leftOperand = leftOperand or Number()
        self.operator = operator
        self.rightOperand = rightOperand or Number()

    def __str__(self) -> str:
        tmpStr = ''
        if self.breakingPrecedence(self.leftOperand):
            tmpStr += '(' + str(self.leftOperand) + ')'
        else:
            tmpStr += str(self.leftOperand)

        tmpStr += ' ' + self.operator.lexeme + ' '

        if self.breakingPrecedence(self.rightOperand):
            tmpStr += '(' + str(self.rightOperand) + ')'
        else:
            tmpStr += str(self.rightOperand)

        return tmpStr

    def setLeftOperand(self, operand: UnaryOperator|MemNode|Number|BinaryOperator|SensorNode) -> None:
        self.leftOperand = operand

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRightOperand(self, operand: UnaryOperator|MemNode|Number|BinaryOperator|SensorNode) -> None:
        self.rightOperand = operand
    
    def evaluate(self) -> int:
        match self.operator.tokenType:
            case TOKENS.T_PLUS:
                return self.leftOperand.evaluate() + self.rightOperand.evaluate()
            case TOKENS.T_MINUS:
                return self.leftOperand.evaluate() - self.rightOperand.evaluate()
            case TOKENS.T_STAR:
                return self.leftOperand.evaluate() * self.rightOperand.evaluate()
            case TOKENS.T_DIV:
                rightOperand = self.rightOperand.evaluate()
                if rightOperand:
                    return self.leftOperand.evaluate() // self.rightOperand.evaluate()
                else:
                    return 0
            case TOKENS.T_MOD:
                rightOperand = self.rightOperand.evaluate()
                if rightOperand:
                    return self.leftOperand.evaluate() % self.rightOperand.evaluate()
                else:
                    return 0
            case _:
                raise ValueError(f'Expected <BinaryOperator> in evaluation. Saw: "{self.operator.lexeme}"')
            
    def breakingPrecedence(self, operand: UnaryOperator|MemNode|Number|BinaryOperator|SensorNode) -> bool:
        if (isinstance(operand, BinaryOperator) and 
            (self.operator.tokenType in SET_MULOPS and 
             operand.operator.tokenType in SET_ADDOPS)):
            return True
        return False

class UnaryOperator(ASTNode):
    _children = ('operator', 'operand')

    def __init__(self, operator: TokenLexeme = T_NONE, operand: UnaryOperator|Number|MemNode|BinaryOperator|SensorNode|None = None) -> None:
        self.operator = operator
        self.operand = operand or Number()

    def __str__(self) -> str:
        return '-' + str(self.operand)

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setOperand(self, operand: UnaryOperator|Number|MemNode|BinaryOperator|SensorNode) -> None:
        self.operand = operand

    def evaluate(self) -> int:
        match self.operator.tokenType:
            case TOKENS.T_MINUS:
                return -(self.operand.evaluate())
            case _:
                raise ValueError(f'Expected <UnaryOperator> in evaluation. Saw: "{self.operator.lexeme}"')

class Number(ASTNode):
    _children = ('number',)

    def __init__(self, number: Token|None = None) -> None:
        if number:
            self.number = TokenLexeme(number.tokenType, number.lexeme)
            self.value = int(self.number.lexeme)
        else:
            self.number = T_NONE
            self.value = 0

    def __str__(self) -> str:
        return self.number.lexeme
    
    def evaluate(self) -> int:
        return self.value

class MemNode(ASTNode):
    _children = ('value', )

    def __init__(self, value: Number|MemNode|UnaryOperator|BinaryOperator|SensorNode|None = None) -> None:
        self.value = value or Number()

    def setValue(self, value: Number|MemNode|UnaryOperator|BinaryOperator|SensorNode) -> None:
        self.value = value

    def getValue(self) -> Number|MemNode|UnaryOperator|BinaryOperator|SensorNode:
        return self.value

    def __str__(self) -> str:
        return f'mem[{self.value}]'
    
    def evaluate(self) -> int:
        return 0
    
    @staticmethod
    def desugar(token: Token) -> MemNode:
        match token.tokenType:
            case TOKENS.T_MEMSIZE:
                number = Number(Token(TOKENS.T_NUMBER, '0', token.line, token.column))
            case TOKENS.T_DEFENSE:
                number = Number(Token(TOKENS.T_NUMBER, '1', token.line, token.column))
            case TOKENS.T_OFFENSE:
                number = Number(Token(TOKENS.T_NUMBER, '2', token.line, token.column))
            case TOKENS.T_SIZE:
                number = Number(Token(TOKENS.T_NUMBER, '3', token.line, token.column))
            case TOKENS.T_ENERGY:
                number = Number(Token(TOKENS.T_NUMBER, '4', token.line, token.column))
            case TOKENS.T_PASS:
                number = Number(Token(TOKENS.T_NUMBER, '5', token.line, token.column))
            case TOKENS.T_POSTURE:
                number = Number(Token(TOKENS.T_NUMBER, '6', token.line, token.column))
            case _:
                raise ValueError(f'Error - Method desugar(token) called with invalid token: {token}')

        memNode = MemNode(number)
        return memNode
    
class SensorNode(ASTNode):
    _children = ('sensorType', 'value')

    def __init__(self, sensorType: Token|None = None, value: Number|MemNode|UnaryOperator|BinaryOperator|SensorNode|None = None) -> None:
        if sensorType:
            self.sensorType = TokenLexeme(sensorType.tokenType, sensorType.lexeme)
        else:
            self.sensorType = T_NONE
        if self.sensorType.tokenType is not TOKENS.T_SMELL:
            self.value = value or Number()
        elif value:
            raise ValueError(f'Unexpected value = {value} for <Sensor> type <Smell>')

    def setSensorType(self, sensorType: Token) -> None:
        self.sensorType = TokenLexeme(sensorType.tokenType, sensorType.lexeme)

    def getSensorType(self) -> TokenLexeme:
        return self.sensorType
    
    def setValue(self, value: Number|MemNode|UnaryOperator|BinaryOperator|SensorNode) -> None:
        if self.sensorType.tokenType is not TOKENS.T_SMELL:
            self.value = value
        else:
            raise ValueError(f'Unexpected value = {value} for <Sensor> type <Smell>')

    def getValue(self) -> Number|MemNode|UnaryOperator|BinaryOperator|SensorNode:
        if self.sensorType.tokenType is not TOKENS.T_SMELL:
            return self.value
        else:
            raise ValueError(f'Cannot return value for <Sensor> type <Smell>')

    def __str__(self) -> str:
        if self.sensorType.tokenType is TOKENS.T_SMELL:
            return f'{self.sensorType.lexeme}'
        return f'{self.sensorType.lexeme}[{self.value}]'
    
    def evaluate(self) -> int:
        return 0