from __future__ import annotations
from typing import Any, ClassVar, Iterator, TypeVar, Generator, TYPE_CHECKING, cast
from schemas import TokenLexeme, TOKENS, Token, SET_MULOPS, SET_ADDOPS, T_NONE
import copy

T = TypeVar("T", bound="ASTNode")


class AbstractSyntaxTree:

    def __init__(self, rootNode: Program | None = None) -> None:
        self.rootNode = rootNode or Program()
        self.nodeCount = countNodes(self.rootNode)
        self.expressions: list[ExpressionNode]

    def _walk(self, currentNode: ASTNode) -> Generator[ASTNode, None, None]:
        yield currentNode
        for child in currentNode:
            yield from self._walk(child)

    def getNodesByType(self, nodeType: type[T]) -> list[T]:
        return [
            node for node in self._walk(self.rootNode) if isinstance(node, nodeType)
        ]

    def copyProgram(self) -> Program:
        program = copy.deepcopy(self.rootNode)

        return program

    def getParentByNode(self, node: ASTNode) -> ASTNode | None:
        for parentCandidate in self._walk(self.rootNode):
            if node in parentCandidate:
                return parentCandidate
        return None


class ASTNode:
    _children: ClassVar[tuple[str, ...]] = ()

    def __iter__(self) -> Iterator[ASTNode]:
        for fieldName in self._children:
            value = getattr(self, fieldName, None)
            if isinstance(value, list):
                yield from (item for item in value if isinstance(item, ASTNode))
            elif isinstance(value, ASTNode):
                yield value

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> bool:
        return False

    def copyNode(self) -> ASTNode:
        return copy.deepcopy(self)


class Program(ASTNode):
    _children = ("rules",)

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules or []

    def __str__(self) -> str:
        return "\n".join(str(rule) for rule in self.rules)

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> bool:
        for i in range(len(self.rules)):
            if self.rules[i] is oldChild:
                self.rules[i] = cast(Rule, newChild)
                return True
        return False


class ExpressionNode(ASTNode):
    def evaluate(self) -> int:
        raise NotImplementedError()


class BooleanOperator(ASTNode):
    _children = ("leftOperand", "rightOperand")

    def __init__(self) -> None:
        # BooleanOperator is an abstraction for RelationalOperator and LogicalOperator
        # It shouldn't get instantiated. The data fields are for code working with
        # one of the two concrete subclasses. We know they both have a left and right operand.
        # This is really just so Pylance doesn't complain when I want to access a left or
        # right operand without having to cast it. I know the field is there, no matter
        # which subclass I actually have.

        if type(self) is BooleanOperator:
            raise TypeError("BooleanOperator should not be directly instantiated.")
        self.leftOperand = BooleanOperator()
        self.rightOperand = BooleanOperator()

    def evaluate(self) -> bool:
        raise NotImplementedError()


class Rule(ASTNode):
    _children = ("condition", "commands")

    def __init__(
        self,
        condition: BooleanOperator | None = None,
        commands: list[Command] | None = None,
    ) -> None:
        self.condition = condition or BooleanOperator()
        self.commands = commands or []

    def __str__(self) -> str:
        result = "\n     ".join(map(str, self.commands))
        return f"{self.condition} --> \n     {result}\n     ;\n"

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> bool:
        if self.condition is oldChild:
            self.condition = newChild
            return True

        for i in range(len(self.commands)):
            if self.commands[i] is oldChild:
                if type(newChild) is Action and i != (len(self.commands) - 1):
                    raise RuntimeError("Action must be final Command")
                self.commands[i] = cast(Update | Action, newChild)
                return True
        return False


class Command(ASTNode):
    def __str__(self) -> str:
        raise NotImplementedError()


class Update(Command):
    _children = ("destination", "source")

    def __init__(
        self, destination: MemNode | None = None, source: ExpressionNode | None = None
    ) -> None:
        self.destination = destination or MemNode()
        self.source = source or ExpressionNode()

    def __str__(self) -> str:
        return f"{self.destination} := {self.source}"


class Action(Command):
    _children = ()

    def __init__(self, actionType: Token | None = None) -> None:
        if actionType:
            self.actionType = TokenLexeme(actionType.tokenType, actionType.lexeme)
        else:
            self.actionType = T_NONE

    def __str__(self) -> str:
        return f"{self.actionType.lexeme}"


class ServeAction(Action):
    _children = ()

    def __init__(
        self, actionType: Token | None = None, value: ExpressionNode | None = None
    ) -> None:
        super().__init__(actionType)
        if value:
            self.value = value
        else:
            self.value = Number()

    def __str__(self) -> str:
        return f"serve[{self.value}]"


class LogicalOperator(BooleanOperator):
    _children = ("leftOperand", "rightOperand")

    def __init__(
        self,
        leftOperand: BooleanOperator | None = None,
        operator: TokenLexeme = T_NONE,
        rightOperand: BooleanOperator | None = None,
    ) -> None:

        self.leftOperand = leftOperand or RelationalOperator()
        self.operator = operator
        self.rightOperand = rightOperand or RelationalOperator()

    def __str__(self) -> str:
        tmpStr = ""

        if self.breakingPrecedence(self.leftOperand):
            tmpStr += "{" + str(self.leftOperand) + "}"
        else:
            tmpStr += str(self.leftOperand)

        tmpStr += " " + self.operator.lexeme + " "

        if self.breakingPrecedence(self.rightOperand):
            tmpStr += "{" + str(self.rightOperand) + "}"
        else:
            tmpStr += str(self.rightOperand)

        return tmpStr

    def evaluate(self) -> bool:
        match self.operator.tokenType:
            case TOKENS.T_AND:
                return self.leftOperand.evaluate() and self.rightOperand.evaluate()
            case TOKENS.T_OR:
                return self.leftOperand.evaluate() or self.rightOperand.evaluate()
            case _:
                raise ValueError(
                    f'Expected <LogicalOperator> in evaluation. Saw: "{self.operator.lexeme}"'
                )

    def breakingPrecedence(self, operand: BooleanOperator) -> bool:
        if isinstance(operand, LogicalOperator) and (
            self.operator.tokenType is TOKENS.T_AND
            and operand.operator.tokenType is TOKENS.T_OR
        ):
            return True
        return False


class RelationalOperator(BooleanOperator):
    _children = ("leftOperand", "rightOperand")

    def __init__(
        self,
        leftOperand: ExpressionNode | None = None,
        operator: TokenLexeme = T_NONE,
        rightOperand: ExpressionNode | None = None,
    ) -> None:
        self.leftOperand = leftOperand or Number()
        self.operator = operator
        self.rightOperand = rightOperand or Number()

    def __str__(self) -> str:
        return (
            str(self.leftOperand)
            + " "
            + self.operator.lexeme
            + " "
            + str(self.rightOperand)
        )

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
                raise ValueError(
                    f'Expected <RelationalOperator> in evaluation. Saw: "{self.operator.lexeme}"'
                )


class BinaryOperator(ExpressionNode):
    _children = ("leftOperand", "rightOperand")

    def __init__(
        self,
        leftOperand: ExpressionNode | None = None,
        operator: TokenLexeme = T_NONE,
        rightOperand: ExpressionNode | None = None,
    ) -> None:
        self.leftOperand = leftOperand or Number()
        self.operator = operator
        self.rightOperand = rightOperand or Number()

    def __str__(self) -> str:
        tmpStr = ""
        if self.breakingPrecedence(self.leftOperand):
            tmpStr += "(" + str(self.leftOperand) + ")"
        else:
            tmpStr += str(self.leftOperand)

        tmpStr += " " + self.operator.lexeme + " "

        if self.breakingPrecedence(self.rightOperand):
            tmpStr += "(" + str(self.rightOperand) + ")"
        else:
            tmpStr += str(self.rightOperand)

        return tmpStr

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
                raise ValueError(
                    f'Expected <BinaryOperator> in evaluation. Saw: "{self.operator.lexeme}"'
                )

    def breakingPrecedence(self, operand: ExpressionNode) -> bool:
        if isinstance(operand, BinaryOperator) and (
            self.operator.tokenType in SET_MULOPS
            and operand.operator.tokenType in SET_ADDOPS
        ):
            return True
        return False


class UnaryOperator(ExpressionNode):
    _children = ("operand",)

    def __init__(
        self, operator: TokenLexeme = T_NONE, operand: ExpressionNode | None = None
    ) -> None:
        self.operator = operator
        self.operand = operand or Number()

    def __str__(self) -> str:
        return "-" + str(self.operand)

    def evaluate(self) -> int:
        match self.operator.tokenType:
            case TOKENS.T_MINUS:
                return -(self.operand.evaluate())
            case _:
                raise ValueError(
                    f'Expected <UnaryOperator> in evaluation. Saw: "{self.operator.lexeme}"'
                )


class Number(ExpressionNode):
    _children = ()

    def __new__(cls, number: Token | None = None, value: int | None = None):
        if number and value is not None:
            raise ValueError(
                "Number can be created from a <Token> or a <Value>, not both."
            )
        candidate: int | None = None
        if number:
            candidate = int(number.lexeme)
        elif value is not None:
            candidate = value
        else:
            return super().__new__(cls)
        if candidate < 0:
            positiveNumber = Number(value=abs(candidate))
            return UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), positiveNumber)
        return super().__new__(cls)

    def __init__(self, number: Token | None = None, value: int | None = None) -> None:
        if number and value is not None:
            raise ValueError(
                "Number can be created from a <Token> or a <Value>, not both."
            )
        if number:
            if int(number.lexeme) < 0:
                raise ValueError(
                    "<Number> cannot be negative. You must create a <UnaryOperator>."
                )
            self._number = TokenLexeme(number.tokenType, number.lexeme)
            self._value = int(self.number.lexeme)
        elif value is not None:
            if value < 0:
                raise ValueError(
                    "<Number> cannot be negative. You must create a <UnaryOperator>."
                )
            self._number = TokenLexeme(TOKENS.T_NUMBER, str(value))
            self._value = value
        else:
            self._number = T_NONE
            self._value = 0

    def __str__(self) -> str:
        return self.number.lexeme

    def evaluate(self) -> int:
        return self._value

    @property
    def number(self) -> TokenLexeme:
        return self._number

    @number.setter
    def number(self, number: TokenLexeme) -> None:
        if int(number.lexeme) < 0:
            raise ValueError(
                "<Number> cannot be negative. You must create a <UnaryOperator>."
            )
        self._number = number
        self._value = int(self._number.lexeme)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        if value < 0:
            raise ValueError(
                "<Number> cannot be negative. You must create a <UnaryOperator>."
            )
        self._number = TokenLexeme(TOKENS.T_NUMBER, str(value))
        self._value = value


class MemNode(ExpressionNode):
    _children = ("value",)

    def __init__(self, value: ExpressionNode | None = None) -> None:
        self.value = value or Number()

    def __str__(self) -> str:
        if isinstance(self.value, Number):
            return MemNode.resugar(self.value.evaluate())
        return f"mem[{self.value}]"

    def __eq__(self, value: object) -> bool:
        if (
            isinstance(value, MemNode)
            and value.value.evaluate() == self.value.evaluate()
        ):
            return True
        return False

    def evaluate(self) -> int:
        return 0

    @staticmethod
    def desugar(token: Token) -> MemNode:
        match token.tokenType:
            case TOKENS.T_MEMSIZE:
                number = Number(Token(TOKENS.T_NUMBER, "0", token.line, token.column))
            case TOKENS.T_DEFENSE:
                number = Number(Token(TOKENS.T_NUMBER, "1", token.line, token.column))
            case TOKENS.T_OFFENSE:
                number = Number(Token(TOKENS.T_NUMBER, "2", token.line, token.column))
            case TOKENS.T_SIZE:
                number = Number(Token(TOKENS.T_NUMBER, "3", token.line, token.column))
            case TOKENS.T_ENERGY:
                number = Number(Token(TOKENS.T_NUMBER, "4", token.line, token.column))
            case TOKENS.T_PASS:
                number = Number(Token(TOKENS.T_NUMBER, "5", token.line, token.column))
            case TOKENS.T_POSTURE:
                number = Number(Token(TOKENS.T_NUMBER, "6", token.line, token.column))
            case _:
                raise ValueError(
                    f"Error - Method desugar(token) called with invalid token: {token}"
                )

        memNode = MemNode(number)
        return memNode

    @staticmethod
    def resugar(value: int) -> str:
        match value:
            case 0:
                return "MEMSIZE"
            case 1:
                return "DEFENSE"
            case 2:
                return "OFFENSE"
            case 3:
                return "SIZE"
            case 4:
                return "ENERGY"
            case 5:
                return "PASS"
            case 6:
                return "POSTURE"
            case _:
                return f"mem[{value}]"


class SensorNode(ExpressionNode):
    _children = ()

    def __init__(self, sensorType: Token | None = None) -> None:
        if sensorType:
            self.sensorType = TokenLexeme(sensorType.tokenType, sensorType.lexeme)
        else:
            self.sensorType = T_NONE

    def __str__(self) -> str:
        return f"{self.sensorType.lexeme}"

    def evaluate(self) -> int:
        return 0


class DirectedSensorNode(SensorNode):
    _children = ("value",)

    def __init__(
        self, sensorType: Token | None = None, value: ExpressionNode | None = None
    ) -> None:
        super().__init__(sensorType)

        self.value: ExpressionNode = value or Number()

    def __str__(self) -> str:
        return f"{self.sensorType.lexeme}[{self.value}]"

    def evaluate(self) -> int:
        return 0


class SmellNode(SensorNode):
    pass


def countNodes(node: ASTNode):
    nodes = 0
    if not isinstance(node, Program):
        nodes = 1  # Don't count the program itself, it is passthrough.
    for child in node:
        nodes += countNodes(child)
    return nodes
