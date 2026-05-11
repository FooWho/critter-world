from __future__ import annotations
from typing import Any, ClassVar, Iterator, TYPE_CHECKING
from schemas import TokenLexeme, T_NONE, TOKENS, Token, SET_MULOPS, SET_ADDOPS

class AbstractSyntaxTree():
    pass
    
class Program(AbstractSyntaxTree):

    def __init__(self, rootNode: RelationalOperator|BinaryOperator|UnaryOperator|Number|MemNode|None = None) -> None:
        self.rootNode = rootNode or Number()
    
    def __str__(self) -> str:
        return ''.join([str(self.rootNode), str(self.rootNode)])
    
    def setRoot(self, root: RelationalOperator|BinaryOperator|UnaryOperator|Number|MemNode) -> None:
        self.rootNode = root

    def getRoot(self) -> RelationalOperator|BinaryOperator|UnaryOperator|Number|MemNode:
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
        return str(self.leftOperand) + ' ' + self.operator.lexeme + ' ' + str(self.rightOperand)

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
                raise ValueError('Bad Relational Operator')



class RelationalOperator(ASTNode):
    _children = ('leftOperand', 'operator', 'rightOperand')

    def __init__(self, leftOperand: UnaryOperator|MemNode|Number|BinaryOperator|None = None, 
                 operator: TokenLexeme = T_NONE, 
                 rightOperand: UnaryOperator|MemNode|Number|BinaryOperator|None = None) -> None:      
        self.leftOperand = leftOperand or Number()
        self.operator = operator
        self.rightOperand = rightOperand or Number()

    def __str__(self) -> str:
        return str(self.leftOperand) + ' ' + self.operator.lexeme + ' ' + str(self.rightOperand)

    def setLeftOperand(self, operand: UnaryOperator|MemNode|Number|BinaryOperator) -> None:
        self.leftOperand = operand

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRightOperand(self, operand: UnaryOperator|MemNode|Number|BinaryOperator) -> None:
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
                raise ValueError('Bad Relational Operator')


class BinaryOperator(ASTNode):
    _children = ('leftOperand', 'operator', 'rightOperand')

    def __init__(self, leftOperand: UnaryOperator|MemNode|Number|BinaryOperator|None = None, 
                 operator: TokenLexeme = T_NONE, 
                 rightOperand: UnaryOperator|MemNode|Number|BinaryOperator|None = None) -> None:      
        self.leftOperand = leftOperand or Number()
        self.operator = operator
        self.rightOperand = rightOperand or Number()

    def __str__(self) -> str:
        tmpStr = ''
        if isinstance(self.leftOperand, BinaryOperator) and (self.operator.tokenType in SET_MULOPS and self.leftOperand.operator.tokenType in SET_ADDOPS):
            tmpStr += '(' + str(self.leftOperand) + ')'
        else:
            tmpStr += str(self.leftOperand)

        tmpStr += ' ' + self.operator.lexeme + ' '

        if isinstance(self.rightOperand, BinaryOperator) and (self.operator.tokenType in SET_MULOPS and self.rightOperand.operator.tokenType in SET_ADDOPS):
            tmpStr += '(' + str(self.rightOperand) + ')'
        else:
            tmpStr += str(self.rightOperand)

        return tmpStr

    def setLeftOperand(self, operand: UnaryOperator|MemNode|Number|BinaryOperator) -> None:
        self.leftOperand = operand

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRightOperand(self, operand: UnaryOperator|MemNode|Number|BinaryOperator) -> None:
        self.rightOperand = operand
    
    def evaluate(self) -> float:
        match self.operator.tokenType:
            case TOKENS.T_PLUS:
                return self.leftOperand.evaluate() + self.rightOperand.evaluate()
            case TOKENS.T_MINUS:
                return self.leftOperand.evaluate() - self.rightOperand.evaluate()
            case TOKENS.T_STAR:
                return self.leftOperand.evaluate() * self.rightOperand.evaluate()
            case TOKENS.T_DIV:
                return self.leftOperand.evaluate() / self.rightOperand.evaluate()
            case _:
                raise ValueError('Bad operator')

class UnaryOperator(ASTNode):
    _children = ('operator', 'operand')

    def __init__(self, operator: TokenLexeme = T_NONE, operand: UnaryOperator|Number|MemNode|BinaryOperator|None = None) -> None:
        self.operator = operator
        self.operand = operand or Number()

    def __str__(self) -> str:
        return '-' + str(self.operand)

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setOperand(self, operand: UnaryOperator|Number|MemNode|BinaryOperator) -> None:
        self.operand = operand

    def evaluate(self) -> float:
        match self.operator.tokenType:
            case TOKENS.T_MINUS:
                return -(self.operand.evaluate())
            case _:
                raise ValueError('Bad operand')

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
    _children: ClassVar[tuple[str]] = ('location',)

    def __init__(self, location: Number|MemNode|UnaryOperator|BinaryOperator|None = None) -> None:
        self.location = location or Number()

    def setLocation(self, location: Number|MemNode|UnaryOperator|BinaryOperator) -> None:
        self.location = location

    def __str__(self) -> str:
        return f'mem[{self.location}]'
    
    def evaluate(self) -> float:
        return 0