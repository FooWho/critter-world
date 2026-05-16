from __future__ import annotations
from typing import cast
import random, math
from schemas import TOKENS, Token, TokenLexeme
from abstractSyntaxTree import (
    AbstractSyntaxTree,
    ASTNode,
    Program,
    ExpressionNode,
    Number,
    UnaryOperator,
    BinaryOperator,
    MemNode,
    DirectedSensorNode,
    RelationalOperator,
    LogicalOperator,
)


class Mutator:

    def __init__(self, mutationProbability: float = 0.0) -> None:
        self.mutationProbability = mutationProbability

    def getWeightedRandom(self):
        loc = random.choice([-1, 1])
        beta = 1.5
        variation = random.expovariate(1 / beta) * random.choice([-1, 1])
        result = int(round(loc + variation))
        if result < -10:
            result = -1
        if result > 10:
            result = 1
        if result == 0:
            result = random.choice([-2, -1, 1, 2])
        return result

        """
        From the original:
        1. Remove: The node, along with all its descendants, is removed. If the parent of the node being removed
        needs a replacement child, one of the node's direct children of the correct kind is randomly selected.
        For example, a rule node is simply removed, whereas a binary operation node would be replaced with either
        its left or its right child. Note that a legal program must contain at least one rule.
        2. Swap: The order of two children of the node is switched. For example, this allows swapping the positions
        of two rules, or changing a - b to b - a.
        3. Replace: The node and its descendants are replaced with a randomly selected subtree of the right kind.
        Randomly selected subtrees are chosen from somewhere in the current AST. The entire AST subtree
        rooted at the selected node is cloned (deep-copied).
        4. Transform: The node is replaced with a random, newly created node of the same kind (for example,
        replacing attack with eat, or + with *), but its children remain the same. Literal integer constants are
        randomly adjusted up or down by the value of java.lang.Integer.MAX_VALUE/r.nextInt(), where
        legal, assuming that r is an object of class java.util.Random.
        5. Insert: A newly created node is inserted as the parent of the mutated node. The old parent of the
        mutated node becomes the parent of the inserted node, and the mutated node becomes a child of the
        inserted node. If the inserted node requires more than one child, the children that are not the original
        node are copies of randomly chosen nodes of the right kind from the entire rule set.
        6. Duplicate: For nodes with a variable number of children, a randomly selected subtree of the right type
        (as in Replace mutations) is appended to the end of the list of children. This applies to the root node,
        where a new rule can be added, and also to command nodes, where the sequence of updates can be
        extended with another update.

        On rule 4, Transform, I am going to make a modification to the original spec. They want to shift integer
        literals up or down by a random value that could be large but is going to be heavily clustered around
        [-1, 1]. My get_weighted_random() method should give a distribution heavily weighted to -1 and 1, with
        tails that fall off rapidly. I am not going to allow a zero. If the mutator decides we are going to change,
        we won't decide to 'change by 0'. I am going to restrict change to [-10, 10].
        """

    def mutate(self, ast: AbstractSyntaxTree, mutations: int) -> bool:
        self.ast: AbstractSyntaxTree = ast
        locus = self.generateFaultLocus(ast)
        match locus[0]:
            case Number():
                locus = cast(tuple[Number, ASTNode], locus)
                new = self.numberFaultInjector(locus)
                match new:
                    case Number():
                        pass
                    case ExpressionNode():
                        parent = locus[1]
                        match parent:
                            case RelationalOperator():
                                parent = cast(RelationalOperator, parent)
                                if locus[0] == parent.getLeftOperand():
                                    parent.setLeftOperand(new)
                                elif locus[0] == parent.getRightOperand():
                                    parent.setRightOperand(new)
                                else:
                                    raise RuntimeError("Couldn't match child.")
                        return True
            case BinaryOperator():
                new = self.binaryOperationFaultInjector(locus[0])
                return True
            case _:
                print("Got skunked")
                return False

    def numberFaultInjector(self, faultLocus: tuple[Number, ASTNode]) -> ExpressionNode:
        choice = random.choice([0, 1])
        numberNode = faultLocus[0]
        parentNode = faultLocus[1]
        match choice:
            case 0:
                amount = self.getWeightedRandom()
                return self.mutateTransformNumber(numberNode, amount)
            case 1:
                return self.mutateInsertNumber(numberNode)
            case _:
                return numberNode

    def mutateTransformNumber(self, number: Number, amount: int) -> Number:
        value = number.getValue()
        value += amount
        return number.setValue(value)

    def mutateInsertNumber(self, number: Number) -> ExpressionNode:
        operator_map = {
            TOKENS.T_ASSIGN: ":=",
            TOKENS.T_LEQU: "<=",
            TOKENS.T_GEQU: ">=",
            TOKENS.T_NEQU: "!=",
            TOKENS.T_LESS: "<",
            TOKENS.T_GREAT: ">",
            TOKENS.T_EQU: "=",
            TOKENS.T_COMM: "-->",
            TOKENS.T_PLUS: "+",
            TOKENS.T_MINUS: "-",
            TOKENS.T_STAR: "*",
            TOKENS.T_DIV: "/",
            TOKENS.T_MOD: "mod",
            TOKENS.T_MEM: "mem",
            TOKENS.T_AHEAD: "ahead",
            TOKENS.T_NEARBY: "nearby",
            TOKENS.T_RANDOM: "random",
        }
        choice = random.choice([0, 1, 2])
        match choice:
            case 0:
                # Insert UnaryOperator
                unaryOperator = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), number)
                return unaryOperator
            case 1:
                # Insert BinaryOperator
                choice = random.choice(
                    [TOKENS.T_MINUS, TOKENS.T_STAR, TOKENS.T_DIV, TOKENS.T_PLUS]
                )
                side = random.choice(["left", "right"])
                op = operator_map.get(choice) or ""
                expressions = self.ast.getExpressions()
                expression = random.choice(expressions)
                otherExpression = cast(ExpressionNode, expression.copyNode())
                if side is "left":
                    return BinaryOperator(
                        leftOperand=number,
                        operator=TokenLexeme(choice, op),
                        rightOperand=otherExpression,
                    )
                else:
                    return BinaryOperator(
                        leftOperand=otherExpression,
                        operator=TokenLexeme(choice, op),
                        rightOperand=number,
                    )
            case 2:
                # Insert MemNode, SensorNode
                choice = random.choice(
                    [TOKENS.T_MEM, TOKENS.T_AHEAD, TOKENS.T_NEARBY, TOKENS.T_RANDOM]
                )
                lexeme = operator_map.get(choice) or ""
                token = Token(choice, lexeme, 0, 0)
                match choice:
                    case TOKENS.T_MEM:
                        return MemNode(number)
                    case TOKENS.T_AHEAD | TOKENS.T_NEARBY | TOKENS.T_RANDOM:
                        return DirectedSensorNode(token, number)
                    case _:
                        return number
            case _:
                unaryOperator = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), number)
                return unaryOperator

    def binaryOperationFaultInjector(
        self, binaryOperation: BinaryOperator
    ) -> BinaryOperator:
        binaryOperation = self.mutateSwapBinaryOperation(binaryOperation)
        return binaryOperation

    def mutateSwapBinaryOperation(
        self, binaryOperation: BinaryOperator
    ) -> BinaryOperator:
        leftOperand = binaryOperation.getLeftOperand()
        rightOperand = binaryOperation.getRightOperand()
        binaryOperation.setLeftOperand(rightOperand)
        binaryOperation.setRightOperand(leftOperand)
        return binaryOperation

    def generateFaultLocus(self, ast: AbstractSyntaxTree) -> tuple[ASTNode, ASTNode]:
        nodeCount = ast.getNodeCount()
        locus = random.randint(1, nodeCount)

        parent: ASTNode = ast.getRoot()
        children = list(parent)
        childPairs = [(child, parent) for child in children]

        stack: list[tuple[ASTNode, ASTNode]] = []
        stack.extend(reversed(childPairs))
        count = 0
        while stack and count <= locus:
            current, parent = stack.pop()
            count += 1
            if count == locus:
                return (current, parent)
            try:
                children = list(current)
                childPairs = [(child, current) for child in children]
                stack.extend(reversed(childPairs))
            except TypeError:
                pass  # This guy has no children
        raise RuntimeError(
            f"Mutator.faultLocus() failed to find a locus of mutation. locus:{locus} nodeCount:{nodeCount}"
        )
