from __future__ import annotations
from typing import Any, ClassVar, Iterator, TYPE_CHECKING
from schemas import TokenLexeme, T_NONE, TOKENS, Token

class AbstractSyntaxTree():

    def __init__(self, rootNode: ASTNode|None = None) -> None:
        self.rootNode = rootNode or ASTNode()

    def getRoot(self) -> ASTNode:
        return self.rootNode
    
class Program(AbstractSyntaxTree):
    
    def __str__(self) -> str:
        return ''.join([str(self.rootNode), str(self.rootNode)])

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

class BinaryOperator(ASTNode):
    _children = ('leftOperand', 'operator', 'rightOperand')

    def __init__(self, leftOperand: UnaryOperator|MemNode|Number|BinaryOperator|None = None, 
                 operator: TokenLexeme = T_NONE, 
                 rightOperand: UnaryOperator|MemNode|Number|BinaryOperator|None = None) -> None:      
        self.leftOperand = leftOperand or Number()
        self.operator = operator
        self.rightOperand = rightOperand or Number()

    def setLeftOperand(self, operand: UnaryOperator|MemNode|Number|BinaryOperator) -> None:
        self.leftOperand = operand

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRightOperand(self, operand) -> None:
        self.rightOperand = operand

    def __str__(self) -> str:
        return ''.join([str(self.leftOperand), ' ', self.operator.lexeme, ' ', str(self.rightOperand)])

class UnaryOperator(ASTNode):
    _children = ('operator', 'operand')

    def __init__(self, operator: TokenLexeme = T_NONE, operand: UnaryOperator|Number|MemNode|BinaryOperator|None = None) -> None:
        self.operator = operator
        self.operand = operand or Number()

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setOperand(self, operand: UnaryOperator|Number|MemNode|BinaryOperator) -> None:
        self.operand = operand

class Number(ASTNode):
    _children = ('number',)

    def __init__(self, number: Token|None = None) -> None:
        if number:
            self.number = TokenLexeme(number.tokenType, number.lexeme)
            self.value = int(self.number.lexeme)
        else:
            self.number = T_NONE
            self.value = None

    def __str__(self) -> str:
        return self.number.lexeme

class MemNode(ASTNode):
    _children: ClassVar[tuple[str]] = ('location',)

    def __init__(self, location: Number|MemNode|UnaryOperator|BinaryOperator|None = None) -> None:
        self.location = location or Number()

    def setLocation(self, location: Number|MemNode|UnaryOperator|BinaryOperator) -> None:
        self.location = location