from __future__ import annotations
from typing import cast
import random, math
from schemas import TOKENS, Token, TokenLexeme
from abstractSyntaxTree import (
    AbstractSyntaxTree,
    countNodes,
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

    operatorMap = {
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

    def __init__(
        self, ast: AbstractSyntaxTree, mutationProbability: float = 0.0
    ) -> None:

        self.ast = ast
        if not self.ast.rootNode:
            raise RuntimeError("AST was not setup in init for Mutator")
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

    def generateFaultLocus(self) -> tuple[ASTNode, ASTNode]:
        if not self.ast.rootNode:
            raise RuntimeError("AST was not setup in init for Mutator")

        nodes = [node for node in self.ast._walk(self.ast.rootNode)]
        nodes.remove(self.ast.rootNode)

        node = random.choice(nodes)
        parent = self.ast.getParentByNode(node)
        if not parent:
            raise RuntimeError(f"Unable to locate parent for {node}")
        return (node, parent)

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

        Currently will always return True or raise an error except in one case - We are attempting to perform
        a Replace operation on a <MemNode> in an AST with only one <MemNode>. In this case, we will return False,
        indicating the mutation failed. Ultimately, I want to clean this up so we "try again", i.e. start the muattion process
        over. This may result in getting rid raising errors, as we can just return False for whatever reason, but probably not.
        Those cases are actually exceptional, typically it means we could not locate a parent or a child in some case
        where we should have.

        """

    def mutate(self, mutations: int) -> bool:

        locus = self.generateFaultLocus()
        match locus[0]:
            case Rule():
                locus = cast(tuple[Rule, Program], locus)
                self.ruleFaultInjector(locus)
                return True
            case Update():
                raise NotImplementedError("updateFaultInjector() not implemented.")
            case Action():
                raise NotImplementedError("actionFaultInjector() not implemented.")
            case LogicalOperator():
                locus = cast(tuple[LogicalOperator, ASTNode], locus)
                self.logicalOperatorFaultInjector(locus)
                return True
            case RelationalOperator():
                locus = cast(tuple[RelationalOperator, ASTNode], locus)
                self.relationalOperatorFaultInjector(locus)
                return True
            case BinaryOperator():
                locus = cast(tuple[BinaryOperator, ASTNode], locus)
                self.binaryOperatorFaultInjector(locus)
                return True
            case UnaryOperator():
                locus = cast(tuple[UnaryOperator, ASTNode], locus)
                self.unaryOperatorFaultInjector(locus)
                return True
            case Number():
                # Numbers are done. Mutations 3, 4, and 5 are supported for all valid cases.
                locus = cast(tuple[Number, ExpressionNode], locus)
                return self.numberFaultInjector(locus)
            case MemNode():
                locus = cast(tuple[MemNode, Update | ExpressionNode], locus)
                return self.memNodeFaultInjector(locus)
            case SensorNode():
                locus = cast(tuple[SensorNode, ASTNode], locus)
                return self.sensorFaultInjector(locus)
            case _:
                print("Got skunked")
                return False

    """
        <RULE>

        There are [n] valid mutations for a <Rule> node - Remove, Swap, Replace, 
    """

    def ruleFaultInjector(self, faultLocus: tuple[Rule, Program]) -> None:
        if not self.ast.rootNode:
            raise RuntimeError("AST was not setup in init for Mutator")
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
        if not self.ast.rootNode:
            raise RuntimeError("AST was not setup in init for Mutator")
        self.ast.rootNode.rules.remove(rule)

    """
        </RULE>
    """

    """
        <NUMBER>

        There are three valid mutation types for a <Number> node - Replace, Transform, and Insert.
        
        A <Number> can't be removed. Doing so would break the expression.

        A <Number> can't be swapped, it doesn't have children.
        
        A <Number> may be replaced by any node subclassed from <ExpressionNode>.
        When a replacement occurs, a randomly selected subtree is selected from the list of
        <ExpressionNodes> in the AST. A copy is performed and the copy is inserted as a subtree
        under the parent of the <Number> node.
        
        A <Number> may be transformed by adding a (positive or negative) integer value. Currenty, 
        this always results results in the creation of a new node that replaces the original,
        i.e. we don't just add to the value. Tyhis could change in the future but probably not.
        The transformation of a <Number> node may result in structural changes to the AST. If a
        positive number becomes negative, a <UnaryOperato> is created to be the parent of the new
        value and it replaces the original <Number> in the parent's subtree. If a negative number
        becomes zero or positive, the <UnaryOperator> that would be the existing parent is removed.
        The new <Number> replaces the <UnaryOperator> in the grandparent subtree.

        A <Number> may be inserted as the child of a newly created node and the new node replaces the
        <Number> in the subtree of the parent. If the newly created node requires additional children
        (for example if the new node is a <BinaryOperator>) the other child is generated by copying
        another node from somewhere else in the AST. In this case, the node to be copied could be any
        node that is a subclass of <ExpressionNode>.

        A <Number> can't be duplicated, it doesn't have a variable number of children.

        numberFaultInjector() will raise NotImplementedError if it is called with a bad faultType
        parameter. This parameter is generally only for testing. In an actual simulation, fault types
        will be randomly selected. numberFaultInjector() will either return True (the mutation was performed),
        or it will raise an exception. We could get rid of the exceptions and return False. This would allow
        us to "try again" either here or in mutate(). Maybe in the future.

    """

    def numberFaultInjector(
        self, faultLocus: tuple[Number, ASTNode], faultType: int | None = None
    ) -> bool:

        if faultType:
            choice = faultType
        else:
            choice = random.choice([3, 4, 5])
        match choice:
            case 3:
                # Replace
                return self.mutateReplaceNumber(faultLocus)
            case 4:
                # Transform
                return self.mutateTransformNumber(faultLocus)
            case 5:
                # Insert
                return self.mutateInsertNumber(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for numberFaultInjector() not implemented."
                )

    def mutateReplaceNumber(
        self,
        faultLocus: tuple[Number, ASTNode],
        mutation: ExpressionNode | None = None,
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        # The selected Number node will be replaced a copy of a randomly selected ExpressionNode from elsewhere in the AST.
        # This mutator will also accept an ExpressionNode to be used for the mutation. This is primarily for use by the unit tests.
        mutation = (
            random.choice(self.ast.getNodesByType(ExpressionNode))
            if not mutation
            else mutation
        )
        mutation = cast(ExpressionNode, mutation.copyNode())
        mutation.ast = parentNode.ast
        # Replace the original child of the parent with the mutation.
        parentNode.replaceChild(originalNode, mutation)
        return True

    def mutateTransformNumber(
        self, faultLocus: tuple[Number, ASTNode], amount: int | None = None
    ) -> bool:

        numberNode = faultLocus[0]
        parentNode = faultLocus[1]

        amount = self.getWeightedRandom() if not amount else amount
        if amount is None:
            amount = self.getWeightedRandom()

        current_value = numberNode.value
        mutationValue = current_value + amount
        mutation = Number(value=mutationValue)
        parentNode.replaceChild(numberNode, mutation)
        return True

    def mutateInsertNumber(
        self, faultLocus: tuple[Number, ASTNode], insertType: int | None = None
    ) -> bool:

        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([1, 2, 3]) if not insertType else insertType
        match choice:
            case 1:
                # Insert UnaryOperator
                mutation = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), originalNode)
            case 2:
                # Insert BinaryOperator
                choice = random.choice(
                    [
                        TOKENS.T_MINUS,
                        TOKENS.T_STAR,
                        TOKENS.T_DIV,
                        TOKENS.T_PLUS,
                        TOKENS.T_MOD,
                    ]
                )
                side = random.choice(["left", "right"])
                op = Mutator.operatorMap.get(choice) or ""
                expressions = self.ast.getNodesByType(ExpressionNode)
                expression = random.choice(expressions)
                otherExpression = cast(ExpressionNode, expression.copyNode())
                if side == "left":
                    mutation = BinaryOperator(
                        leftOperand=originalNode,
                        operator=TokenLexeme(choice, op),
                        rightOperand=otherExpression,
                    )
                else:
                    mutation = BinaryOperator(
                        leftOperand=otherExpression,
                        operator=TokenLexeme(choice, op),
                        rightOperand=originalNode,
                    )
            case 3:
                # Insert MemNode, DirectedSensorNode
                choice = random.choice(
                    [TOKENS.T_MEM, TOKENS.T_AHEAD, TOKENS.T_NEARBY, TOKENS.T_RANDOM]
                )
                lexeme = Mutator.operatorMap.get(choice) or ""
                token = Token(choice, lexeme, 0, 0)
                match choice:
                    case TOKENS.T_MEM:
                        mutation = MemNode(originalNode)
                    case TOKENS.T_AHEAD | TOKENS.T_NEARBY | TOKENS.T_RANDOM:
                        mutation = DirectedSensorNode(token, originalNode)
                    case _:
                        raise RuntimeError(
                            "This shouln't happen - mutateInsertNumber()."
                        )
            case _:
                raise RuntimeError("This should never happen.")

        parentNode.replaceChild(originalNode, mutation)
        return True

    """
        </NUMBER>
    """

    def binaryOperatorFaultInjector(
        self, faultLocus: tuple[BinaryOperator, ASTNode]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([2])
        match choice:
            case 2:
                # swap
                return self.mutateSwapBinaryOperator(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for binaryOperationFaultInjector() not implimented."
                )

    def mutateSwapBinaryOperator(
        self, faultLocus: tuple[BinaryOperator, ASTNode]
    ) -> bool:
        originalNode = faultLocus[0]
        # We aren't going to "collapse" double negatives here. A UnaryOperator is fundamentally different from
        # a BinaryOperator that happens to be subtraction.
        tmp = originalNode.leftOperand
        originalNode.leftOperand = originalNode.rightOperand
        originalNode.rightOperand = tmp
        return True

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

    def sensorFaultInjector(self, faultLocus: tuple[SensorNode, ASTNode]) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([0])
        match choice:
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for sensorFaultInjector() not implemented."
                )

    """
        There are 2 valid mutation types for a <MemNode> - Replace, Insert.
        
        We will not allow Remove - a <MemNode> would just get replaced by the expression that resolved its location. Probably not
        interesting or funcitonal. We could change this in the future.

        We will not allow Swap, a MemNode has a single child.

        Replace is allowed. Targets depend on what the <MemNode> is. If it is the destination for an Update, valid target must be a <MemNode>.
        Otherwise, anything subclassed from <ExpressionNode> is valid.

        Transform is not allowed, there isn't a differnet kind of MemNode to become.

        Insert is allowed, depending on what the <MemNode> is. If the <MemNode> is the destination of an <Update>, 
        the inserted node must also be a MemNode. For other instances, the inserted node can be anything subclassed from
        <ExpressionNode>.

        Duplicate is not allowed, as <MemNode> does not have variable childen.

    """

    def memNodeFaultInjector(
        self,
        faultLocus: tuple[MemNode, Update | ExpressionNode],
        faultType: int | None = None,
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        # We allow Insert (5) on Update destinations as well, handled securely in mutateInsertMemNode
        choice = faultType if faultType is not None else random.choice([3, 5])
        match choice:
            case 3:
                # Replace
                return self.mutateReplaceMemNode(faultLocus)
            case 5:
                # Insert
                return self.mutateInsertMemNode(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for memNodeFaultInjector() not implemented."
                )

    def mutateReplaceMemNode(
        self, faultLocus: tuple[MemNode, ASTNode], mutation: ASTNode | None = None
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        if isinstance(parentNode, Update) and originalNode is parentNode.destination:
            # If the parent is an Update destination, the replacement must be another MemNode
            # If we are the only <MemNode>, we have a problem
            if mutation is None and len(self.ast.getNodesByType(MemNode)) == 1:
                return False
            if mutation is None:
                mutation = random.choice(self.ast.getNodesByType(MemNode))
                while mutation is originalNode:
                    mutation = random.choice(self.ast.getNodesByType(MemNode))
            mutation = cast(MemNode, mutation.copyNode())
        else:
            # If the parent is not an Update destination, the MemNode is part of an Expression
            # and can be replaced by any ExpressionNode
            if mutation is None:
                mutation = random.choice(self.ast.getNodesByType(ExpressionNode))
            mutation = cast(ExpressionNode, mutation.copyNode())
        parentNode.replaceChild(originalNode, mutation)
        return True

    def mutateInsertMemNode(
        self, faultLocus: tuple[MemNode, ASTNode], insertType: int | None = None
    ) -> bool:
        if not self.ast.rootNode:
            raise RuntimeError("AST was not setup in init for Mutator")
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        # If the MemNode is an Update destination, the only valid structural insertion is another MemNode
        if isinstance(parentNode, Update) and originalNode is parentNode.destination:
            choice = 3
        else:
            choice = (
                insertType if insertType is not None else random.choice([0, 1, 2, 3])
            )
        match choice:
            case 0:
                # UnaryOperator
                mutation = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), originalNode)
            case 1:
                # BinaryOperator
                choice = random.choice(
                    [
                        TOKENS.T_MINUS,
                        TOKENS.T_STAR,
                        TOKENS.T_DIV,
                        TOKENS.T_PLUS,
                        TOKENS.T_MOD,
                    ]
                )
                side = random.choice(["left", "right"])
                op = Mutator.operatorMap.get(choice) or ""
                expressions = self.ast.getNodesByType(ExpressionNode)
                expression = random.choice(expressions)
                otherExpression = cast(ExpressionNode, expression.copyNode())
                if side == "left":
                    mutation = BinaryOperator(
                        leftOperand=originalNode,
                        operator=TokenLexeme(choice, op),
                        rightOperand=otherExpression,
                    )
                else:
                    mutation = BinaryOperator(
                        leftOperand=otherExpression,
                        operator=TokenLexeme(choice, op),
                        rightOperand=originalNode,
                    )
            case 2:
                # DirectedSensorNode
                choice = random.choice(
                    [TOKENS.T_AHEAD, TOKENS.T_NEARBY, TOKENS.T_RANDOM]
                )
                lexeme = Mutator.operatorMap.get(choice) or ""
                token = Token(choice, lexeme, 0, 0)
                mutation = DirectedSensorNode(token, originalNode)
            case 3:
                # MemNode (Pointer / Indirect Addressing)
                mutation = MemNode(originalNode)
            case _:
                raise RuntimeError("This shouldn't happen.")

        parentNode.replaceChild(originalNode, mutation)
        return True

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
