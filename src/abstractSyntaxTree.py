from __future__ import annotations
from typing import Any, ClassVar, Iterator, TypeVar, Generator, TYPE_CHECKING, cast
from schemas import TokenLexeme, TOKENS, Token, SET_MULOPS, SET_ADDOPS, T_NONE
import copy

T = TypeVar("T", bound="ASTNode")


class AbstractSyntaxTree:

    def __init__(self, rootNode: Program | None = None) -> None:
        self.rootNode = rootNode
        if self.rootNode:
            self.nodeCount = countNodes(self.rootNode)
            for node in self._walk(self.rootNode):
                node.ast = self

    def _walk(self, currentNode: ASTNode) -> Generator[ASTNode, None, None]:
        yield currentNode
        for child in currentNode:
            yield from self._walk(child)

    def getNodesByType(self, nodeType: type[T]) -> list[T]:
        if self.rootNode:
            return [
                node for node in self._walk(self.rootNode) if isinstance(node, nodeType)
            ]
        return []

    def copyProgram(self) -> Program:
        program = copy.deepcopy(self.rootNode) if self.rootNode else Program()
        return program

    def getParentByNode(self, node: ASTNode) -> ASTNode:
        if self.rootNode:
            for parentCandidate in self._walk(self.rootNode):
                if any(child is node for child in parentCandidate):
                    return parentCandidate
        raise RuntimeError("No Parent when getParentByNode() was called!")


class ASTNode:
    _children: ClassVar[tuple[str, ...]] = ()

    def __init__(self) -> None:
        self.ast: AbstractSyntaxTree = AbstractSyntaxTree()

    def __iter__(self) -> Iterator[ASTNode]:
        for fieldName in self._children:
            value = getattr(self, fieldName, None)
            if isinstance(value, list):
                yield from (item for item in value if isinstance(item, ASTNode))
            elif isinstance(value, ASTNode):
                yield value

    """
    replaceChild() is responsible for updating the nodeCount in the AST and for setting the AST of the 
    newly created child correctly! replaceChild() will raise NotImplimentedError if it is somehow
    being called on a concrete instance of one of the abstract node types. For example, there should not
    be any instances of <ExpressionNode>. If replaceChild is called on a node that is actually of type
    ExpressionNode (shouldn't happen) this will raise the NotImplementedError. It will raise RuntimeError
    if for some reason the correct nodes cannot be located for replacement. If either of these occurs,
    something is broken somewhere else. The parser should not be capable of generating a malformed AST.
    Either there is bug in the mutator, or we are in a unittest and screwed up creating test data.
    """

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        raise NotImplementedError("replaceChild() not implemented for ASTNode.")

    def copyNode(self) -> ASTNode:
        return copy.deepcopy(self)


class Program(ASTNode):
    _children = ("rules",)

    def __init__(
        self,
        rules: list[Rule] | None = None,
    ) -> None:
        super().__init__()
        self.rules = rules or []

    def __str__(self) -> str:
        return "\n".join(str(rule) for rule in self.rules)

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        for i, rule in enumerate(self.rules):
            if rule is oldChild:
                self.rules[i] = cast(Rule, newChild)
                newChild.ast = self.ast
                self.ast.nodeCount += countNodes(newChild) - countNodes(oldChild)
                return
        raise RuntimeError(f"Unable to replace {oldChild} with {newChild} for {self}.")

    def removeChild(self, child: Rule) -> None:
        if len(self.rules) == 1:
            raise RuntimeError(f"Unable to remove {child} for {self}.")

        for i, rule in enumerate(self.rules):
            if rule is child:
                del self.rules[i]
                self.ast.nodeCount -= countNodes(child)
                return
        raise RuntimeError(f"Unable to remove {child} for {self}.")

    def swapChildren(self, firstChild: Rule, secondChild: Rule) -> None:
        firstLocation = -1
        secondLocation = -1

        for i, rule in enumerate(self.rules):
            if rule is firstChild:
                firstLocation = i
            if rule is secondChild:
                secondLocation = i
            if firstLocation >= 0 and secondLocation >= 0:
                break

        if firstLocation < 0 or secondLocation < 0:
            raise RuntimeError(f"Unable to swap {firstChild} and {secondChild}.")
        tmp = self.rules[firstLocation]
        self.rules[firstLocation] = self.rules[secondLocation]
        self.rules[secondLocation] = tmp

    def insertChild(self, child: ASTNode, location: int) -> None:
        child = cast(Rule, child)
        self.rules.insert(location, child)
        child.ast = self.ast
        self.nodeCount += countNodes(child)


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
        super().__init__()
        if type(self) is BooleanOperator:
            # This won't execute, but it makes Pylance happy when referencing left and right operands for RelationalOperator and LogicalOperator generically.
            self.leftOperand = BooleanOperator()
            self.rightOperand = BooleanOperator()

    def evaluate(self) -> bool:
        raise NotImplementedError()

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        oldChild = cast(BooleanOperator, oldChild)
        newChild = cast(BooleanOperator, newChild)
        if self.leftOperand is oldChild:
            self.leftOperand = newChild
        elif self.rightOperand is oldChild:
            self.rightOperand = newChild
        else:
            raise RuntimeError(
                f"Unable to replace {oldChild} with {newChild} for {self}."
            )
        newChild.ast = self.ast
        self.ast.nodeCount += countNodes(newChild) - countNodes(oldChild)


class Rule(ASTNode):
    _children = ("condition", "commands")

    def __init__(
        self,
        condition: BooleanOperator | None = None,
        commands: list[Command] | None = None,
    ) -> None:
        super().__init__()
        self.condition = condition or RelationalOperator()
        self.commands = commands or []

    def __str__(self) -> str:
        result = "\n     ".join(map(str, self.commands))
        return f"{self.condition} --> \n     {result}\n     ;\n"

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        if self.condition is oldChild:
            self.condition = newChild
        elif isinstance(newChild, Command):
            replaced = False
            for i, cmd in enumerate(self.commands):
                if cmd is oldChild:
                    if type(newChild) is Action and oldChild is not self.commands[-1]:
                        raise RuntimeError("Action must be final Command")
                    self.commands[i] = newChild
                    replaced = True
                    break
            if not replaced:
                raise RuntimeError(
                    f"Unable to replace {oldChild} with {newChild} for {self}."
                )
        else:
            raise RuntimeError(
                f"Unable to replace {oldChild} with {newChild} for {self}."
            )
        newChild.ast = self.ast
        self.ast.nodeCount += countNodes(newChild) - countNodes(oldChild)

    def swapChildren(self, firstChild: Command, secondChild: Command) -> None:
        if type(firstChild) is Action or type(secondChild) is Action:
            raise RuntimeError(f"Unable to swap {firstChild} and {secondChild}.")

        firstIndex = -1
        secondIndex = -1
        for i, cmd in enumerate(self.commands):
            if cmd is firstChild:
                firstIndex = i
            if cmd is secondChild:
                secondIndex = i
        if firstIndex >= 0 and secondIndex >= 0:
            tmp = self.commands[firstIndex]
            self.commands[firstIndex] = self.commands[secondIndex]
            self.commands[secondIndex] = tmp
        else:
            raise RuntimeError(f"Unable to swap {firstChild} and {secondChild}.")

    def insertChild(self, newChild: ASTNode, location: int) -> None:
        newChild = cast(Command, newChild)
        self.commands.insert(location, newChild)
        newChild.ast = self.ast
        self.ast.nodeCount += countNodes(newChild)


class Command(ASTNode):
    def __str__(self) -> str:
        raise NotImplementedError()


class Update(Command):
    _children = ("destination", "source")

    def __init__(
        self,
        destination: MemNode | None = None,
        source: ExpressionNode | None = None,
    ) -> None:
        super().__init__()
        self.destination = destination or MemNode()
        self.source = source or Number()

    def __str__(self) -> str:
        return f"{self.destination} := {self.source}"

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        if self.destination is oldChild:
            self.destination = newChild
        elif self.source is oldChild:
            self.source = newChild
        else:
            raise RuntimeError(
                f"Unable to replace {oldChild} with {newChild} for {self}."
            )
        newChild.ast = self.ast
        self.ast.nodeCount += countNodes(newChild) - countNodes(oldChild)


class Action(Command):
    _children = ()

    def __init__(
        self,
        actionType: Token | None = None,
    ) -> None:
        super().__init__()
        if actionType:
            self.actionType = TokenLexeme(actionType.tokenType, actionType.lexeme)
        else:
            self.actionType = T_NONE

    def __str__(self) -> str:
        return f"{self.actionType.lexeme}"


class ServeAction(Action):
    _children = ("value",)

    def __init__(
        self,
        actionType: Token | None = None,
        value: ExpressionNode | None = None,
    ) -> None:
        super().__init__(actionType)
        if value:
            self.value = value
        else:
            self.value = Number()

    def __str__(self) -> str:
        return f"serve[{self.value}]"

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        if self.value is oldChild:
            self.value = newChild
        else:
            raise RuntimeError(
                f"Unable to replace {oldChild} with {newChild} for {self}."
            )
        newChild.ast = self.ast
        self.ast.nodeCount += countNodes(newChild) - countNodes(oldChild)


class LogicalOperator(BooleanOperator):
    _children = ("leftOperand", "rightOperand")

    def __init__(
        self,
        leftOperand: BooleanOperator | None = None,
        operator: TokenLexeme = T_NONE,
        rightOperand: BooleanOperator | None = None,
    ) -> None:
        super().__init__()
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
        super().__init__()
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
        super().__init__()
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

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        oldChild = cast(ExpressionNode, oldChild)
        newChild = cast(ExpressionNode, newChild)

        if self.leftOperand is oldChild:
            self.leftOperand = newChild
        elif self.rightOperand is oldChild:
            self.rightOperand = newChild
        else:
            raise RuntimeError(
                f"Unable to replace {oldChild} with {newChild} for {self}."
            )
        newChild.ast = self.ast
        self.ast.nodeCount += countNodes(newChild) - countNodes(oldChild)

    def swapChildren(
        self, firstChild: ExpressionNode, secondChild: ExpressionNode
    ) -> None:
        if self.leftOperand is firstChild:
            tmp = self.leftOperand
            self.leftOperand = self.rightOperand
            self.rightOperand = tmp
        elif self.rightOperand is firstChild:
            tmp = self.rightOperand
            self.rightOperand = self.leftOperand
            self.leftOperand = tmp
        else:
            raise RuntimeError(
                f"Unable to swap {firstChild} with {secondChild} for {self}."
            )

    def transformOperator(self, newOperator: str) -> None:
        match newOperator:
            case "+":
                self.operator = TokenLexeme(TOKENS.T_PLUS, "+")
            case "-":
                self.operator = TokenLexeme(TOKENS.T_MINUS, "-")
            case "*":
                self.operator = TokenLexeme(TOKENS.T_STAR, "*")
            case "/":
                self.operator = TokenLexeme(TOKENS.T_DIV, "/")
            case "mod":
                self.operator = TokenLexeme(TOKENS.T_MOD, "mod")
            case _:
                raise RuntimeError(
                    f"Unable to replace {self.operator} with {newOperator} for {self}."
                )


class UnaryOperator(ExpressionNode):
    _children = ("operand",)

    def __init__(
        self,
        operator: TokenLexeme = T_NONE,
        operand: ExpressionNode | None = None,
    ) -> None:
        super().__init__()
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

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        oldChild = cast(ExpressionNode, oldChild)
        newChild = cast(ExpressionNode, newChild)

        if self.operand is oldChild:
            self.operand = newChild
        else:
            raise RuntimeError(
                f"Unable to replace {oldChild} with {newChild} for {self}."
            )
        newChild.ast = self.ast
        self.ast.nodeCount += countNodes(newChild) - countNodes(oldChild)


class Number(ExpressionNode):
    _children = ()

    def __new__(
        cls,
        number: Token | None = None,
        value: int | None = None,
    ):
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

    def __init__(
        self,
        number: Token | None = None,
        value: int | None = None,
    ) -> None:
        super().__init__()
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

    def __init__(
        self,
        value: ExpressionNode | None = None,
    ) -> None:
        super().__init__()
        self.value = value or Number()

    def __str__(self) -> str:
        if isinstance(self.value, Number):
            return MemNode.resugar(self.value.evaluate())
        return f"mem[{self.value}]"

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

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        oldChild = cast(ExpressionNode, oldChild)
        newChild = cast(ExpressionNode, newChild)

        if self.value is oldChild:
            self.value = newChild
        else:
            raise RuntimeError(
                f"Unable to replace {oldChild} with {newChild} for {self}."
            )
        newChild.ast = self.ast
        self.ast.nodeCount += countNodes(newChild) - countNodes(oldChild)


class SensorNode(ExpressionNode):
    _children = ()

    def __init__(
        self,
        sensorType: Token | None = None,
    ) -> None:
        super().__init__()
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
        self,
        sensorType: Token | None = None,
        value: ExpressionNode | None = None,
    ) -> None:
        super().__init__(
            sensorType,
        )

        self.value: ExpressionNode = value or Number()

    def __str__(self) -> str:
        return f"{self.sensorType.lexeme}[{self.value}]"

    def evaluate(self) -> int:
        return 0

    def replaceChild(self, oldChild: ASTNode, newChild: ASTNode) -> None:
        oldChild = cast(ExpressionNode, oldChild)
        newChild = cast(ExpressionNode, newChild)

        if self.value is oldChild:
            self.value = newChild
        else:
            raise RuntimeError(
                f"Unable to replace {oldChild} with {newChild} for {self}."
            )
        newChild.ast = self.ast
        self.ast.nodeCount += countNodes(newChild) - countNodes(oldChild)


class SmellNode(SensorNode):
    pass


def countNodes(node: ASTNode):
    nodes = 1
    for child in node:
        nodes += countNodes(child)
    return nodes
