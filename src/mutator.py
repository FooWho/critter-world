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
    SensorNode,
    RelationalOperator,
    LogicalOperator,
    Update,
    Action,
    Rule,
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
        [-1, 1]. My getWeightedRandom() method should give a distribution heavily weighted to -1 and 1, with
        tails that fall off rapidly. I am not going to allow a zero. If the mutator decides we are going to change,
        we won't decide to 'change by 0'. I am going to restrict change to [-10, 10].

        Will need validations before it's done. For example, remove rule currently just removes the
        stated rule. A program with no rules is not valid, so we can't pick to do this if there is only
        one rule.
        """

    def mutate(self, ast: AbstractSyntaxTree, mutations: int) -> bool:

        self.ast: AbstractSyntaxTree = ast
        locus = self.generateFaultLocus(ast)
        match locus[0]:
            case Number():
                locus = cast(tuple[Number, ExpressionNode], locus)
                self.numberFaultInjector(locus)
                return True
            case MemNode():
                locus = cast(tuple[MemNode, ASTNode], locus)
                self.memNodeFaultInjector(locus)
                return True
            case SensorNode():
                locus = cast(tuple[SensorNode, ASTNode], locus)
                self.sensorFaultInjector(locus)
                return True
            case BinaryOperator():
                locus = cast(tuple[BinaryOperator, ASTNode], locus)
                self.binaryOperatorFaultInjector(locus)
                return True
            case LogicalOperator():
                locus = cast(tuple[LogicalOperator, ASTNode], locus)
                self.logicalOperatorFaultInjector(locus)
                return True
            case RelationalOperator():
                locus = cast(tuple[RelationalOperator, ASTNode], locus)
                self.relationalOperatorFaultInjector(locus)
                return True
            case Rule():
                locus = cast(tuple[Rule, Program], locus)
                self.ruleFaultInjector(locus)
                return True
            case UnaryOperator():
                locus = cast(tuple[UnaryOperator, ASTNode], locus)
                self.unaryOperatorFaultInjector(locus)
                return True
            case Update():
                raise NotImplementedError("updateFaultInjector() not implemented.")
            case Action():
                raise NotImplementedError("actionFaultInjector() not implemented.")
            case _:
                print("Got skunked")
                return False

    def numberFaultInjector(self, faultLocus: tuple[Number, ExpressionNode]) -> None:

        choice = random.choice([4, 5])
        match choice:
            case 4:
                # Transform
                self.mutateTransformNumber(faultLocus)
            case 5:
                # Insert
                self.mutateInsertNumber(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for numberFaultInjector() not implemented."
                )

    def mutateTransformNumber(self, faultLocus: tuple[Number, ExpressionNode]) -> None:

        numberNode = faultLocus[0]
        parentNode = faultLocus[1]
        amount = self.getWeightedRandom()
        numberNode.value += amount

    def mutateInsertNumber(self, faultLocus: tuple[Number, ExpressionNode]) -> None:
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
        numberNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([0, 1, 2])
        match choice:
            case 0:
                # Insert UnaryOperator
                unaryOperator = UnaryOperator(
                    TokenLexeme(TOKENS.T_MINUS, "-"), numberNode
                )
                self.updateInsertion(unaryOperator, faultLocus)
            case 1:
                # Insert BinaryOperator
                choice = random.choice(
                    [TOKENS.T_MINUS, TOKENS.T_STAR, TOKENS.T_DIV, TOKENS.T_PLUS]
                )
                side = random.choice(["left", "right"])
                op = operator_map.get(choice) or ""
                expressions = self.ast.getNodesByType(ExpressionNode)
                expression = random.choice(expressions)
                otherExpression = cast(ExpressionNode, expression.copyNode())
                if side == "left":
                    binaryOperator = BinaryOperator(
                        leftOperand=numberNode,
                        operator=TokenLexeme(choice, op),
                        rightOperand=otherExpression,
                    )
                else:
                    binaryOperator = BinaryOperator(
                        leftOperand=otherExpression,
                        operator=TokenLexeme(choice, op),
                        rightOperand=numberNode,
                    )
                self.updateInsertion(binaryOperator, faultLocus)
            case 2:
                # Insert MemNode, SensorNode
                choice = random.choice(
                    [TOKENS.T_MEM, TOKENS.T_AHEAD, TOKENS.T_NEARBY, TOKENS.T_RANDOM]
                )
                lexeme = operator_map.get(choice) or ""
                token = Token(choice, lexeme, 0, 0)
                match choice:
                    case TOKENS.T_MEM:
                        memNode = MemNode(numberNode)
                        self.updateInsertion(memNode, faultLocus)
                    case TOKENS.T_AHEAD | TOKENS.T_NEARBY | TOKENS.T_RANDOM:
                        sensorNode = DirectedSensorNode(token, numberNode)
                        self.updateInsertion(sensorNode, faultLocus)
                    case _:
                        raise RuntimeError(
                            "This shouln't happen - mutateInsertNumber()."
                        )
            case _:
                raise RuntimeError("This should never happen.")

    def binaryOperatorFaultInjector(
        self, faultLocus: tuple[BinaryOperator, ASTNode]
    ) -> None:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([2])
        match choice:
            case 2:
                # swap
                self.mutateSwapBinaryOperator(originalNode)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for binaryOperationFaultInjector() not implimented."
                )

    def mutateSwapBinaryOperator(self, binaryOperator: BinaryOperator) -> None:
        tmp = binaryOperator.leftOperand
        binaryOperator.leftOperand = binaryOperator.rightOperand
        binaryOperator.rightOperand = tmp

    def relationalOperatorFaultInjector(
        self, faultLocus: tuple[RelationalOperator, ASTNode]
    ) -> None:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([0])
        match choice:
            case 2:
                self.mutateSwapRelationalOperator(originalNode)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for relationOperationFaultInjector() not implimented."
                )

    def mutateSwapRelationalOperator(
        self, relationalOperator: RelationalOperator
    ) -> None:
        tmp = relationalOperator.leftOperand
        relationalOperator.leftOperand = relationalOperator.rightOperand
        relationalOperator.rightOperand = tmp

    def logicalOperatorFaultInjector(
        self, faultLocus: tuple[LogicalOperator, ASTNode]
    ) -> None:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([2])
        match choice:
            case 2:
                self.mutateSwapLogicalOperator(originalNode)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for logicalOperatorFaultInjector() not implemented."
                )

    def mutateSwapLogicalOperator(self, logicalOperator: LogicalOperator) -> None:
        tmp = logicalOperator.leftOperand
        logicalOperator.leftOperand = logicalOperator.rightOperand
        logicalOperator.rightOperand = tmp

    def ruleFaultInjector(self, faultLocus: tuple[Rule, Program]) -> None:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([1])
        match choice:
            case 1:
                self.ast.rootNode.rules.remove(originalNode)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for ruleFaultInjector() not implemented."
                )

    def mutateRemoveRuleFaultInjector(self, rule: Rule) -> None:
        self.ast.rootNode.rules.remove(rule)

    def sensorFaultInjector(self, faultLocus: tuple[SensorNode, ASTNode]) -> None:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([0])
        match choice:
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for sensorFaultInjector() not implemented."
                )

    def memNodeFaultInjector(self, faultLocus: tuple[MemNode, ASTNode]) -> None:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([0])
        match choice:
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for memNodeFaultInjector() not implemented."
                )

    def unaryOperatorFaultInjector(
        self, faultLocus: tuple[UnaryOperator, ASTNode]
    ) -> None:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([0])
        match choice:
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for unaryOperatorFaultInjector() not implemented."
                )

    def generateFaultLocus(self, ast: AbstractSyntaxTree) -> tuple[ASTNode, ASTNode]:
        nodeCount = ast.nodeCount
        locus = random.randint(1, nodeCount)

        parent: ASTNode = ast.rootNode
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

    def updateInsertion(self, mutation: ExpressionNode, locus: tuple[Number, ASTNode]):
        originalNode = locus[0]
        parentNode = locus[1]
        match parentNode:
            case UnaryOperator():
                parentNode.operand = mutation
            case RelationalOperator():
                print(f"We got a {type(mutation)}")
                if originalNode == parentNode.leftOperand:
                    parentNode.leftOperand = mutation
                elif originalNode == parentNode.rightOperand:
                    parentNode.rightOperand = mutation
                else:
                    raise RuntimeError("Couldn't match the child in updateInsertion()")
            case Update():
                parentNode.source = mutation
            case BinaryOperator():
                if parentNode.leftOperand == originalNode:
                    parentNode.leftOperand = mutation
                elif parentNode.rightOperand == originalNode:
                    parentNode.rightOperand = mutation
                else:
                    raise RuntimeError("We did not match the left or right operand.")
            case DirectedSensorNode():
                parentNode.value = mutation
            case _:
                print("IN DEFAULT")
                print(
                    f"We got a (mutation) {type(mutation)} (parent) {type(parentNode)}"
                )
