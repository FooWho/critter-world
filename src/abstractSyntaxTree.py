from __future__ import annotations
from typing import ClassVar, Iterator, TYPE_CHECKING
from schemas import TokenLexeme, Token, TOKENS, T_NONE, SET_SENSORS

class AbstractSyntaxTree():

    def __init__(self, rootNode: ASTNode|None = None) -> None:
        self.rootNode = rootNode or ASTNode()

    def getRoot(self) -> ASTNode:
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

class Program(ASTNode):
    _children = ('obj',)

    def __init__(self, obj: Term|Factor|BinaryOperator|Number|None = None) -> None:
        self.obj:list[Term|Factor|BinaryOperator|Number] = []
        if obj:
            self.obj.append(obj)

    def addObj(self, obj: Term|Factor|BinaryOperator|Number) -> None:
        self.obj.append(obj)

class Sensor(ASTNode):
    _children = ('sensor',)

    def __init__(self, sensorType: Token|None = None, expression: Expression|None = None) -> None:
        self.expression = expression or Expression()
        sensorType = sensorType or Token(TOKENS.T_NONE, '', 0, 0)
        self.sensorType = next((item.name for item in SET_SENSORS if item.name is (sensorType.tokenType.name)), None)
        

class MemNode(ASTNode):
    _children = ('expression',)

    def __init__(self, expression: Expression|None = None) -> None:
        self.expression = expression or Expression()

    def __str__(self)-> str:
        return f'mem[{str(self.expression)}]'
    
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
        factor = Factor(number)
        term = Term(factor)
        expression = Expression(term)
        memNode = MemNode(expression)
        return memNode
            

class Expression(ASTNode):
    _children = ('expression',)

    def __init__(self, expression: Term|BinaryOperator|None = None) -> None:
       self.expression = expression or Term()

    def __str__(self) -> str:
       return str(self.expression)
    
    def setExpression(self, expression: Term|BinaryOperator) -> None:
        self.expression = expression

class BinaryOperator(ASTNode):
    _children = ('leftSide', 'operator', 'rightSide')

    def __init__(self, leftSide: Term|Factor|BinaryOperator|None = None, operator: TokenLexeme|None = None, rightSide: Term|Factor|BinaryOperator|None = None) -> None:
        self.leftSide = leftSide or Factor()
        self.operator = operator or T_NONE
        self.rightSide = rightSide or Factor()
    
    def __str__(self) -> str:
        return str(self.leftSide) + ' ' + self.operator.lexeme + ' ' + str(self.rightSide)
    
    def setLeft(self, leftSide: Term|Factor|BinaryOperator) -> None:
        self.leftSide = leftSide

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRight(self, rightSide: Term|Factor|BinaryOperator) -> None:
        self.rightSide = rightSide

class UnaryOperator(ASTNode):
    _children = ('operator', 'operand')

    def __init__(self, operator: TokenLexeme|None = None, operand: Factor|None = None) -> None:
        self.operator = operator or T_NONE
        self.operand = operand or Factor()

    def __str__(self) -> str:
        return '-' + str(self.operand)
    
    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setOperand(self, operand: Factor) ->None:
        self.operand = operand

class Term(ASTNode):
    _children = ('term',)

    def __init__(self, term: Factor|BinaryOperator|None = None) -> None:
        self.term = term or Factor()

    def __str__(self) -> str:
        return str(self.term)
    
    def setTerm(self, term: Factor|BinaryOperator) -> None:
        self.term = term

class Factor(ASTNode):
    _children = ('factor',)

    def __init__(self, factor: Number|MemNode|UnaryOperator|Expression|None = None) -> None:
        self.factor = factor or Number()
        self.factorType: TOKENS
        match self.factor:
            case Number():
                self.factorType = TOKENS.T_NUMBER
            case MemNode():
                self.factorType = TOKENS.T_MEM
            case UnaryOperator():
                self.factorType = TOKENS.T_MINUS
            case Expression():
                self.factorType = TOKENS.T_L_PAREN
            case _:
                raise ValueError(f'Error: Received unexpected type for Factor: {str(type(self.factor))}')
    
    def setFactor(self, factor: Number|MemNode|UnaryOperator|Expression) -> None:
        self.factor = factor
        match self.factor:
            case Number():
                self.factorType = TOKENS.T_NUMBER
            case MemNode():
                self.factorType = TOKENS.T_MEM
            case UnaryOperator():
                self.factorType = TOKENS.T_MINUS
            case Expression():
                self.factorType = TOKENS.T_L_PAREN
            case _:
                raise ValueError(f'Error: Received unexpected type for Factor: {str(type(self.factor))}')

    def __str__(self) -> str:
        return str(self.factor)
    
class Number(ASTNode):
    _children = ('number',)

    def __init__(self, number: Token|None = None) -> None:
        if number:
            self.number = TokenLexeme(number.tokenType, number.lexeme)
        else:
            self.number = T_NONE

    def __str__(self) -> str:
        return self.number.lexeme

        


