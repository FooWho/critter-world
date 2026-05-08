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

    def __init__(self, obj: Condition|None = None) -> None:
        self.obj:list[Condition] = []
        if obj:
            self.obj.append(obj)

    def addObj(self, obj: Condition) -> None:
        self.obj.append(obj)

class SensorNode(ASTNode):
    _children = ('sensor',)

    def __init__(self, sensorType: Token|None = None, expression: Expression|None = None) -> None:
        self.expression = expression or Expression()
        if sensorType:
            self.sensorType = sensorType.tokenType
        else:
            self.sensorType = TOKENS.T_NONE

    def __str__(self) -> str:
        match self.sensorType:
            case TOKENS.T_AHEAD:
                return f'ahead[{str(self.expression)}]'
            case TOKENS.T_NEARBY:
                return f'nearby[{str(self.expression)}]'
            case TOKENS.T_RANDOM:
                return f'random[{str(self.expression)}]'
            case TOKENS.T_SMELL:
                return 'smell'
            case _:
                raise 

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
    

class Condition(ASTNode):
    _children = ('condition',)

    def __init__(self, condition: LogicalOperator|RelationalOperator|None = None, needsBrace: bool = False) -> None:
        self.condition = condition or RelationalOperator()
        self.needsBrace = needsBrace        
            
    def setCondition(self, condition: LogicalOperator|RelationalOperator, needsBrace: bool = False) -> None:
        self.condition = condition
        self.needsBrace = needsBrace

class Conjunction(ASTNode):
    _children = ('conjunction',)

    def __init__(self, conjunction: RelationalOperator|LogicalOperator|None = None) -> None:
        self.conjunction = conjunction or RelationalOperator()

    def setConjunction(self, conjunction: RelationalOperator|LogicalOperator) -> None:
        self.conjunction = conjunction


class Expression(ASTNode):
    _children = ('expression',)

    def __init__(self, expression: Term|BinaryOperator|None = None) -> None:
       self.expression = expression or Term()

    def __str__(self) -> str:
       return str(self.expression)
    
    def setExpression(self, expression: Term|BinaryOperator) -> None:
        self.expression = expression

    @staticmethod
    def expressionIsTerm(this: Term|BinaryOperator):
        return isinstance(this, Term)
    
class LogicalOperator(ASTNode):
    _children = ('leftSide', 'operator', 'righSide')

    def __init__(self, leftSide: RelationalOperator|Conjunction|LogicalOperator|None = None, operator: TokenLexeme|None = None, rightSide: RelationalOperator|LogicalOperator|Conjunction|None = None) -> None:
        self.leftSide = leftSide or RelationalOperator()
        self.operator = operator or T_NONE
        self.rightSide = rightSide or RelationalOperator()

    def __str__(self) -> str:
        return ''.join([str(self.leftSide), ' ', self.operator.lexeme, ' ', str(self.rightSide)])
    
    def setLeft(self, leftSide: RelationalOperator|LogicalOperator|Conjunction) -> None:
        self.leftSide = leftSide

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRight(self, rightSide: RelationalOperator|LogicalOperator|Conjunction) -> None:
        self.rightSide = rightSide

class BinaryOperator(ASTNode):
    _children = ('leftSide', 'operator', 'rightSide')

    def __init__(self, leftSide: Term|Factor|BinaryOperator|None = None, operator: TokenLexeme|None = None, rightSide: Term|Factor|BinaryOperator|None = None) -> None:
        self.leftSide = leftSide or Factor()
        self.operator = operator or T_NONE
        self.rightSide = rightSide or Factor()
    
    def __str__(self) -> str:
        return ''.join([str(self.leftSide), ' ', self.operator.lexeme, ' ', str(self.rightSide)])
    
    def setLeft(self, leftSide: Term|Factor|BinaryOperator) -> None:
        self.leftSide = leftSide

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRight(self, rightSide: Term|Factor|BinaryOperator) -> None:
        self.rightSide = rightSide

class RelationalOperator(ASTNode):
    _children = ('leftSide', 'operator', 'rightSide')

    def __init__(self, leftSide: Expression|None = None, operator: TokenLexeme|None = None, rightSide: Expression|None = None) -> None:
        self.leftSide = leftSide or Expression()
        self.operator = operator or T_NONE
        self.rightSide = rightSide or Expression()

    def __str__(self) -> str:
        return ''.join([str(self.leftSide), ' ', self.operator.lexeme, ' ', str(self.rightSide)])
    
    def setLeft(self, leftSide: Expression) -> None:
        self.leftSide = leftSide

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRight(self, rightSide: Expression) -> None:
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

    def __init__(self, factor: Number|MemNode|UnaryOperator|Expression|SensorNode|None = None) -> None:
        self.factor = factor or Number()
        self.factorType: TOKENS
        match self.factor:
            case Number():
                self.factorType = TOKENS.T_NUMBER
            case MemNode():
                self.factorType = TOKENS.T_MEM
            case SensorNode():
                self.factorType = self.factor.sensorType
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
        if self.factorType is TOKENS.T_L_PAREN:
            return ''.join(['(', str(self.factor),')'])
        else:
            return str(self.factor)
               
    
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
    

        


