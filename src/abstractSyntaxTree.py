from __future__ import annotations
from typing import ClassVar, Iterator, TYPE_CHECKING
from schemas import TokenLexeme, Token, TOKENS, T_NONE

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
        

class MemNode(ASTNode):
    _children = ('expression',)

    def __init__(self, expression: Expression|None = None) -> None:
        self.expression = expression or Expression()

    def __str__(self)-> str:
        return f'mem[{str(self.expression)}]'

class Expression(ASTNode):
    _children = ('expression',)

    def __init__(self, expression: Term|BinaryOperator|None = None) -> None:
       self.expression = expression or Term()

    def __str__(self) -> str:
       return str(self.expression)
    
    def setExpression(self, expression: Expression|BinaryOperator) -> None:
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

    def __init__(self, factor: Number|MemNode|UnaryOperator|None = None) -> None:
        self.factor = factor or Number()
        self.factorType: TOKENS
        match self.factor:
            case Number():
                self.factorType = TOKENS.T_NUMBER
            case MemNode():
                self.factorType = TOKENS.T_MEM
            case UnaryOperator():
                self.factorType = TOKENS.T_MINUS
            case _:
                raise ValueError(f'Error: Received unexpected type for Factor: {str(type(self.factor))}')
    
    def setFactor(self, factor: Number|MemNode|UnaryOperator) -> None:
        self.factor = factor
        match self.factor:
            case Number():
                self.factorType = TOKENS.T_NUMBER
            case MemNode():
                self.factorType = TOKENS.T_MEM
            case UnaryOperator():
                self.factorType = TOKENS.T_MINUS
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

        


