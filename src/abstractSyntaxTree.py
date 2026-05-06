from __future__ import annotations
from typing import ClassVar, Iterator, TYPE_CHECKING
from schemas import TokenLexeme, TOKENS, T_NONE

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
    _children = ('tofob',)

    def __init__(self, tofob: Term|Factor|BinaryOperator|None = None) -> None:
        self.tofob = tofob or Factor()
        

    """
    def addNumber(self, number: Number) -> None:
        self.numbers.append(number)
    """

    def addTermOrFactorOrBinary(self, tofob: Term|Factor|BinaryOperator) -> None:
        self.tofob = tofob


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

    def __init__(self, factor: Number|None = None) -> None:
        self.factor = factor or Number(T_NONE)
    
    def setFactor(self, factor: Number) -> None:
        self.factor = factor

    def __str__(self) -> str:
        return str(self.factor)
    
class Number(ASTNode):
    _children = ('number',)

    def __init__(self, number: TokenLexeme|None = None) -> None:
        self.number = number or T_NONE

    def __str__(self) -> str:
        return self.number.lexeme

        


