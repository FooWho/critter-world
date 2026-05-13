from __future__ import annotations
from typing import Any, ClassVar, Iterator
from schemas import TokenLexeme, TOKENS, Token, SET_MULOPS, SET_ADDOPS, T_NONE
import copy
import random

class AbstractSyntaxTree():
    
    def __init__(self, rootNode: Program|None = None) -> None:
        self.rootNode = rootNode or Program()

    def setRoot(self, rootNode: Program) -> None:
        self.rootNode = rootNode

    def getRoot(self) -> Program:
        return self.rootNode
    
    def copyAST(self, mutationProbability: float = 0.0) -> AbstractSyntaxTree:
        program = copy.deepcopy(self.rootNode)
        if (random.random() < mutationProbability):
            if (random.random() < 0.50):
                # Attribute mutation
                attribute = random.randint(0, 2)
                match attribute:
                    case 0:
                        # Memsize
                        pass
                    case 1:
                        # Offense
                        pass
                    case 2:
                        # Defense
                        pass
            else:
                # Rule mutation
                pass

        return AbstractSyntaxTree(program)
    
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
    _children = ('rules', )

    def __init__(self, rules: list[Rule]|None = None) -> None:
        self.rules = rules or []
    
    def __str__(self) -> str:
        return '\n'.join(str(rule) for rule in self.rules)
    
    def addRule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def getRules(self) -> list[Rule]:
        return self.rules

class ExpressionNode(ASTNode):
    def evaluate(self) -> int:
        raise NotImplementedError()

class BooleanOperator(ASTNode):
    def evaluate(self) -> bool:
        raise NotImplementedError()

class Rule(ASTNode):
    _children = ('condition', 'commandBlock')

    def __init__(self, condition: BooleanOperator|None = None, commandBlock: CommandBlock|None = None) -> None:
        self.condition = condition or BooleanOperator()
        self.commandBlock = commandBlock or CommandBlock()

    def __str__(self) -> str:
        return f'{str(self.condition)} --> \n     {str(self.commandBlock)}\n     ;\n'
    
    def setRule(self, condition: BooleanOperator, commandBlock: CommandBlock) -> None:
        self.condition = condition
        self.commandBlock = commandBlock

    def setCondition(self, condition: BooleanOperator) -> None:
        self.condition = condition
    
    def setCommandBlock(self, commandBlock: CommandBlock) -> None:
        self.commandBlock = commandBlock

    def addCommand(self, command: Command) -> None:
        self.commandBlock.addCommand(command)

class CommandBlock(ASTNode):
    _children = ('commands',)

    def __init__(self, commands: list[Command]|None = None) -> None:
        self.commands = commands or []

    def firstCommand(self, command: Command) -> None:
        if self.commands:
            raise ValueError('FirstCommand called for CommandBlock with existing commands.')
        self.commands.append(command)

    def addCommand(self, command: Command) -> None:
        if self.commands and isinstance(self.commands[-1], Action):
            raise ValueError('<CommandBlock> not allowed to have <Command> following a terminal <Action>.')
        self.commands.append(command)

    def __str__(self) -> str:
        result = '\n     '.join(map(str, self.commands))
        return f'{result}'
    
        

class Command(ASTNode):
    def __str__(self) -> str:
        raise NotImplementedError()

class Update(Command):
    _children = ('destination', 'source')

    def __init__(self, destination: MemNode|None = None, source: ExpressionNode|None = None) -> None:
        self.destination = destination or MemNode()
        self.source = source or ExpressionNode()

    def __str__(self) -> str:
        return f'{self.destination} := {self.source}'
    
    def setUpdate(self, destination: MemNode, source: ExpressionNode) -> None:
        self.destination = destination
        self.source = source

    def setDestination(self, destination: MemNode) -> None:
        self.destination = destination

    def setSource(self, source: ExpressionNode) -> None:
        self.source = source


class Action(Command):
    _children = ('actionType',)

    def __init__(self, actionType: Token|None = None) -> None:
        if actionType:
            self.actionType = TokenLexeme(actionType.tokenType, actionType.lexeme)
        else:
            self.actionType = T_NONE

    def __str__(self) -> str:
        return f'{self.actionType.lexeme}'
    

class ServeAction(Action):
    _children = ('actionType', 'value')

    def __init__(self, actionType: Token|None = None, 
                 value: ExpressionNode|None = None) -> None:
        super().__init__(actionType)
        if value:
            self.value = value
        else:
            self.value = Number()

    def __str__(self) -> str:
        return f'serve[{str(self.value)}]'



class LogicalOperator(BooleanOperator):
    _children = ('leftOperand', 'operator', 'rightOperand')

    def __init__(self, leftOperand: BooleanOperator|None = None, 
                 operator: TokenLexeme = T_NONE, 
                 rightOperand: BooleanOperator|None = None) -> None:  
            
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

    def setLeftOperand(self, operand: BooleanOperator) -> None:
        self.leftOperand = operand

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRightOperand(self, operand: BooleanOperator) -> None:
        self.rightOperand = operand

    def evaluate(self) -> bool:
        match self.operator.tokenType:
            case TOKENS.T_AND:
                return self.leftOperand.evaluate() and self.rightOperand.evaluate()
            case TOKENS.T_OR:
                return self.leftOperand.evaluate() or self.rightOperand.evaluate()
            case _:
                raise ValueError(f'Expected <LogicalOperator> in evaluation. Saw: "{self.operator.lexeme}"')
            
    def breakingPrecedence(self, operand: BooleanOperator) -> bool:
        if (isinstance(operand, LogicalOperator) and 
            (self.operator.tokenType is TOKENS.T_AND and 
             operand.operator.tokenType is TOKENS.T_OR)):
            return True
        return False

class RelationalOperator(BooleanOperator):
    _children = ('leftOperand', 'operator', 'rightOperand')

    def __init__(self, leftOperand: ExpressionNode|None = None, 
                 operator: TokenLexeme = T_NONE, 
                 rightOperand: ExpressionNode|None = None) -> None:      
        self.leftOperand = leftOperand or Number()
        self.operator = operator
        self.rightOperand = rightOperand or Number()

    def __str__(self) -> str:
        return str(self.leftOperand) + ' ' + self.operator.lexeme + ' ' + str(self.rightOperand)

    def setLeftOperand(self, operand: ExpressionNode) -> None:
        self.leftOperand = operand

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRightOperand(self, operand: ExpressionNode) -> None:
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


class BinaryOperator(ExpressionNode):
    _children = ('leftOperand', 'operator', 'rightOperand')

    def __init__(self, leftOperand: ExpressionNode|None = None, 
                 operator: TokenLexeme = T_NONE, 
                 rightOperand: ExpressionNode|None = None) -> None:      
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

    def setLeftOperand(self, operand: ExpressionNode) -> None:
        self.leftOperand = operand

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setRightOperand(self, operand: ExpressionNode) -> None:
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
            
    def breakingPrecedence(self, operand: ExpressionNode) -> bool:
        if (isinstance(operand, BinaryOperator) and 
            (self.operator.tokenType in SET_MULOPS and 
             operand.operator.tokenType in SET_ADDOPS)):
            return True
        return False

class UnaryOperator(ExpressionNode):
    _children = ('operator', 'operand')

    def __init__(self, operator: TokenLexeme = T_NONE, operand: ExpressionNode|None = None) -> None:
        self.operator = operator
        self.operand = operand or Number()

    def __str__(self) -> str:
        return '-' + str(self.operand)

    def setOperator(self, operator: TokenLexeme) -> None:
        self.operator = operator

    def setOperand(self, operand: ExpressionNode) -> None:
        self.operand = operand

    def evaluate(self) -> int:
        match self.operator.tokenType:
            case TOKENS.T_MINUS:
                return -(self.operand.evaluate())
            case _:
                raise ValueError(f'Expected <UnaryOperator> in evaluation. Saw: "{self.operator.lexeme}"')

class Number(ExpressionNode):
    _children = ('number', 'value')

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

class MemNode(ExpressionNode):
    _children = ('value', )

    def __init__(self, value: ExpressionNode|None = None) -> None:
        self.value = value or Number()

    def setValue(self, value: ExpressionNode) -> None:
        self.value = value

    def getValue(self) -> ExpressionNode:
        return self.value

    def __str__(self) -> str:
        if isinstance(self.value, Number):
            return MemNode.resugar(self.value.evaluate())
        return f'mem[{str(self.value)}]'
    
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
    
    @staticmethod
    def resugar(value: int) -> str:
        match value:
            case 0:
                return 'MEMSIZE'
            case 1:
                return 'DEFENSE'
            case 2:
                return 'OFFENSE'
            case 3:
                return 'SIZE'
            case 4:
                return 'ENERGY'
            case 5:
                return 'PASS'
            case 6:
                return 'POSTURE'
            case _:
                return f'mem[{value}]'
    
class SensorNode(ExpressionNode):
    _children = ('sensorType',)

    def __init__(self, sensorType: Token|None = None) -> None:
        if sensorType:
            self.sensorType = TokenLexeme(sensorType.tokenType, sensorType.lexeme)
        else:
            self.sensorType = T_NONE

    def setSensorType(self, sensorType: Token) -> None:
        self.sensorType = TokenLexeme(sensorType.tokenType, sensorType.lexeme)

    def getSensorType(self) -> TokenLexeme:
        return self.sensorType

    def __str__(self) -> str:
        return f'{self.sensorType.lexeme}'
    
    def evaluate(self) -> int:
        return 0
    
class DirectedSensorNode(SensorNode):
    _children = ('sensorType', 'value')

    def __init__(self, sensorType: Token|None = None, value: ExpressionNode|None = None) -> None:
        super().__init__(sensorType)

        self.value = value or Number()

    def setValue(self, value: ExpressionNode) -> None:
        self.value = value

    def getValue(self) -> ExpressionNode:
        return self.value

    def __str__(self) -> str:
        return f'{self.sensorType.lexeme}[{self.value}]'
    
    def evaluate(self) -> int:
        return 0
    
class SmellNode(SensorNode):
    pass