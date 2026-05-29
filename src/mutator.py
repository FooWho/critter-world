from __future__ import annotations
from typing import cast
from enum import Enum
import random, math
from schemas import (
    TOKENS,
    Token,
    TokenLexeme,
    SET_ACTIONS,
    SET_RELOPS,
    SET_LOGICOPS,
    SET_ADDOPS,
    SET_MULOPS,
)
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
    BooleanOperator,
    Update,
    Action,
    Command,
    Rule,
)


class Side(Enum):
    LEFT = 0
    RIGHT = 1


class Mutations(Enum):
    REMOVE = 1
    SWAP = 2
    REPLACE = 3
    TRANSFORM = 4
    INSERT = 5
    DUPLICATE = 6


class NodeType(Enum):
    UNARY_OPERATOR = 1
    BINARY_OPERATOR = 2
    MEMNODE = 3
    DIRECTED_SENSOR_NODE = 4


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
        TOKENS.T_AND: "and",
        TOKENS.T_OR: "or",
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

        nodes = list(self.ast._walk(self.ast.rootNode))

        node = random.choice(nodes)

        if node is self.ast.rootNode:
            # The parent of the Program node is the AST itself.
            # This makes the type hint wrong, but we handle it correctly
            # down the line. The cast is a null op anyway.
            return (node, cast(ASTNode, self.ast))

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

        My Notes:
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

        Names of the mutations are kind of confusing. For example, A "swap" mutatation swaps the postion of children of
        the node selected for mutation, but a "remove" mutation removes the node selected for mutation. So sometimes the
        action is happening on the node selected for mutation, other times it is happening on the children. Something
        is always happening to the selected node, but it sometimes feels more like a side effect.
        """

    def mutate(self, mutations: int) -> bool:

        mutationsApplied = 0
        attempts = 0
        maxAttempts = mutations * 100

        while mutationsApplied < mutations and attempts < maxAttempts:
            attempts += 1
            locus = self.generateFaultLocus()
            success = False

            match locus[0]:
                case Program():
                    locus = cast(tuple[Program, AbstractSyntaxTree], locus)
                    success = self.programFaultInjector(locus)
                case Rule():
                    locus = cast(tuple[Rule, Program], locus)
                    success = self.ruleFaultInjector(locus)
                case Update():
                    raise NotImplementedError("updateFaultInjector() not implemented.")
                case Action():
                    raise NotImplementedError("actionFaultInjector() not implemented.")
                case LogicalOperator():
                    locus = cast(tuple[LogicalOperator, Rule | LogicalOperator], locus)
                    success = self.logicalOperatorFaultInjector(locus)
                case RelationalOperator():
                    locus = cast(
                        tuple[RelationalOperator, LogicalOperator | Rule], locus
                    )
                    success = self.relationalOperatorFaultInjector(locus)
                case BinaryOperator():
                    locus = cast(
                        tuple[BinaryOperator, ExpressionNode | RelationalOperator],
                        locus,
                    )
                    success = self.binaryOperatorFaultInjector(locus)
                case UnaryOperator():
                    locus = cast(
                        tuple[UnaryOperator, ExpressionNode | RelationalOperator], locus
                    )
                    success = self.unaryOperatorFaultInjector(locus)
                case Number():
                    locus = cast(tuple[Number, ExpressionNode], locus)
                    success = self.numberFaultInjector(locus)
                case MemNode():
                    locus = cast(tuple[MemNode, Update | ExpressionNode], locus)
                    success = self.memNodeFaultInjector(locus)
                case SensorNode():
                    locus = cast(tuple[SensorNode, ASTNode], locus)
                    success = self.sensorFaultInjector(locus)
                case _:
                    success = False

            if success:
                mutationsApplied += 1

        return mutationsApplied == mutations

    """
        <PROGRAM>

        There are 2 valid mutations for a <Program> node - Swap and Duplicate.

        Remove does not make sense, because we would eliminate the entire program.

        Swap does work. If the program has at least two <Rule> nodes, swap their locations in the list of rules.

        Replace does not work. We can't just completely replace the program with a different program.

        Transform does not work. There is nothing to transform the program into.

        Insert does not work, we can't insert a new parent above the progam node.

        Duplicate works. We can randomly select a Rule and insert it into the list of rules.
    """

    def programFaultInjector(
        self, faultLocus: tuple[Program, AbstractSyntaxTree]
    ) -> bool:

        choice = random.choice([Mutations.SWAP, Mutations.DUPLICATE])

        match choice:
            case Mutations.SWAP:
                return self.mutateSwapProgram(faultLocus)
            case Mutations.DUPLICATE:
                return self.mutateDuplicateProgram(faultLocus)

        return False

    def mutateSwapProgram(self, faultLocus: tuple[Program, AbstractSyntaxTree]) -> bool:

        originalNode = faultLocus[0]
        length = len(originalNode.rules)
        if length < 2:
            # A swap can't be performed if we only have one rule.
            return False

        targets = random.sample(originalNode.rules, 2)
        originalNode.swapChildren(targets[0], targets[1])
        return True

    def mutateDuplicateProgram(
        self, faultLocus: tuple[Program, AbstractSyntaxTree], target: Rule | None = None
    ) -> bool:
        originalNode = faultLocus[0]

        if not target:
            candidates = self.ast.getNodesByType(Rule)
            if not candidates:
                # There were no Rule nodes in the AST.
                # This shouldn't happen, so we will raise exception instead of return False
                raise RuntimeError(f"{originalNode} has no rules!")
            target = random.choice(candidates)

        target = cast(Rule, target.copyNode())
        length = len(originalNode.rules)
        location = random.randint(0, length)
        originalNode.insertChild(target, location)
        return True

    """
        </PROGRAM
    """

    """
        <RULE>

        There are 4 valid mutations for a <Rule> node - Remove, Swap, Replace, and Duplicate.

        A <Rule> can be removed, as long as there is at least one rule remaining. If we try to remove the last <Rule> we will return False.
        Otherwise, the rule is removed and the critter has one less rule in its ruleset.

        A <Rule> can have a swap, if it's command block has multiple <Updates>. An <Update> and an <Action> can't swap, as an action must
        be the last command in a command block. We will return False if we are trying to swap and there is not a valid node to swap with.

        A <Rule> can be replaced, unless there is only one rule, in which case we will return False. Grab another rule at random,
        copy it, and put it in the slot occupied by this rule.

        A transform is not valid. There is nothing to change the rule into, while keeping its children.

        An insert is not valid. The parent of a rule is the program, we can't create another program, put the rule in as a child, 
        and then attach the new program as a child of the original program.

        A duplicate can be performed by randomly selecting a <Command> from some other location in the AST and inserting it into
        a random location in the command block, as long as it precedes the Action (if present). If the <Rule> does not have an
        Action, the duplication can be to insert an Action as the last Command.
    """

    def ruleFaultInjector(self, faultLocus: tuple[Rule, Program]) -> bool:

        choice = random.choice(
            [Mutations.REMOVE, Mutations.SWAP, Mutations.REPLACE, Mutations.DUPLICATE]
        )
        match choice:
            case Mutations.REMOVE:
                return self.mutateRemoveRule(faultLocus)
            case Mutations.SWAP:
                return self.mutateSwapRule(faultLocus)
            case Mutations.REPLACE:
                return self.mutateReplaceRule(faultLocus)
            case Mutations.DUPLICATE:
                return self.mutateDuplicateRule(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for ruleFaultInjector() not implemented."
                )

    def mutateRemoveRule(self, faultLocus: tuple[Rule, Program]) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        if len(parentNode.rules) == 1:
            # If we are the only rule, we can't be removed, but this was a valid path to follow.
            # Return False
            return False
        parentNode.removeChild(originalNode)
        return True

    def mutateSwapRule(self, faultLocus: tuple[Rule, Program]) -> bool:
        originalNode = faultLocus[0]

        if isinstance(originalNode.commands[-1], Action):
            # Final command is an action
            if len(originalNode.commands) >= 3:
                # But there are at least 2 other commands, we can perform a swap.
                targets = random.sample(originalNode.commands[:-1], 2)
                originalNode.swapChildren(targets[0], targets[1])
                return True
            return False
        else:
            # There is no Action as a final command
            if len(originalNode.commands) >= 2:
                # We only need two elements to swap.
                targets = random.sample(originalNode.commands, 2)
                originalNode.swapChildren(targets[0], targets[1])
                return True
            return False

    def mutateReplaceRule(self, faultLocus: tuple[Rule, Program]) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        if len(parentNode.rules) == 1:
            # If there is only one rule, we can't do a replacement.
            return False

        candidates = [rule for rule in parentNode.rules if rule is not originalNode]
        otherRule = random.choice(candidates)
        parentNode.replaceChild(originalNode, otherRule.copyNode())
        return True

    def mutateDuplicateRule(
        self, faultLocus: tuple[Rule, Program], target: Command | None = None
    ) -> bool:
        originalNode = faultLocus[0]

        candidates = []
        if not target:
            candidates = self.ast.getNodesByType(Command)
            target = random.choice(candidates)

        hasAction = isinstance(originalNode.commands[-1], Action)

        if isinstance(target, Action):
            if hasAction:
                # A rule can only have one Action
                return False
            location = len(originalNode.commands)
        else:
            length = len(originalNode.commands)
            if hasAction:
                location = random.randint(0, length - 1)
            else:
                location = random.randint(0, length)

        originalNode.insertChild(target.copyNode(), location)
        return True

    """
        </RULE>
    """

    """
        <UPDATE>

        There are 3 valid mutation types for an Update - Remove, Swap, and Replace.

        An Update may be removed, as long as the parent Rule has at least one other Command.

        An Update may have the destination and source swapped, but only if both are MemNodes.

        An Update may be replaced. Randomly select a different Update from elsewhere in the AST and take the place of this Update.
    """

    def updateFaultInjector(self, faultLocus: tuple[Update, Rule]) -> bool:

        choice = random.choice([Mutations.REMOVE, Mutations.SWAP, Mutations.REPLACE])

        match choice:
            case Mutations.REMOVE:
                return self.mutateUpdateRemove(faultLocus)
            case Mutations.SWAP:
                return self.mutateUpdateSwap(faultLocus)
            case Mutations.REPLACE:
                return self.mutateUpdateReplace(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for updateFaultInjector() not implemented."
                )

        return False

    def mutateUpdateRemove(self, faultLocus: tuple[Update, Rule]) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        length = len(parentNode.commands)
        if length == 1:
            # We can't have a rule with no commands, this mutation fails.
            return False
        parentNode.removeChild(originalNode)
        return True

    def mutateUpdateSwap(self, faultLocus: tuple[Update, Rule]) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        if not isinstance(originalNode.destination, MemNode) or not isinstance(
            originalNode.source, MemNode
        ):
            # We can only swap if both the destination and the source are MemNodes, as we must end up with a MemNode as the destination.
            return False

        originalNode.swapChildren()
        return True

    def mutateUpdateReplace(self, faultLocus: tuple[Update, Rule]) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        candidates = [
            update
            for update in self.ast.getNodesByType(Update)
            if update is not originalNode
        ]
        if not candidates:
            # No valid candidates to replace me, so this mutation fails.
            return False
        candidate = random.choice(candidates).copyNode()
        parentNode.replaceChild(originalNode, candidate)
        return True

    """
        </UPDATE>
    """

    """
        <ACTION>
        There are 3 valid mutations for an Action node - Remove, Replace, and Transform.

        An Action node may be removed, so long as the Rule has at least one other Command.

        An Action may be replaced by selecting a random Action from elsewhere in the AST, copying it and putting it
        int the place of this Action.

        An Action may be transformed by changing it to an Action of a different type, for example, "wait" could
        be tranformed to "forward".
    """

    def actionFaultInjector(
        self, faultLocus: tuple[Action, Rule], faultType: Mutations | None = None
    ) -> bool:
        if not faultType:
            faultType = random.choice(
                [Mutations.REMOVE, Mutations.REPLACE, Mutations.TRANSFORM]
            )

        match faultType:
            case Mutations.REMOVE:
                return self.mutateActionRemove(faultLocus)
            case Mutations.REPLACE:
                return self.mutateActionReplace(faultLocus)
            case Mutations.TRANSFORM:
                return self.mutateActionTransform(faultLocus)
            case _:
                raise RuntimeError(
                    f"{faultType} for actionFaultInjector() not implemented."
                )
        return False

    def mutateActionRemove(self, faultLocus: tuple[Action, Rule]) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        if len(parentNode.commands) == 1:
            # We can't remove the only Command a Rule has
            return False
        parentNode.removeChild(originalNode)
        return True

    def mutateActionReplace(
        self, faultLocus: tuple[Action, Rule], mutation: Action | None = None
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        mutation = (
            random.choice(
                [
                    selection
                    for selection in self.ast.getNodesByType(Action)
                    if selection is not originalNode
                ]
            )
            if not mutation
            else mutation
        )
        if not mutation:
            # There were no valid selections
            return False
        mutation = cast(Action, mutation.copyNode())
        parentNode.replaceChild(originalNode, mutation)
        return True

    def mutateActionTransform(
        self, faultLocus: tuple[Action, Rule], targetTokenType: TOKENS | None = None
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        candidates = list(SET_ACTIONS)
        if originalNode.actionType.tokenType in candidates:
            candidates.remove(originalNode.actionType.tokenType)

        newTokenType = targetTokenType if targetTokenType else random.choice(candidates)

        expr = None
        if newTokenType == TOKENS.T_SERVE:
            exprCandidates = self.ast.getNodesByType(ExpressionNode)
            if exprCandidates:
                expr = cast(ExpressionNode, random.choice(exprCandidates).copyNode())

        mutation = originalNode.transformAction(newTokenType, expr)
        parentNode.replaceChild(originalNode, mutation)
        return True

    """
        </ACTION
    """

    """
        <LOGICAL_OPERATOR>

        There are 5 valid mutations for a LogicalOperator node - Remove, Swap, Replace, Transform, and Insert.

        A LogicalOperator can be removed. For example, a Rule with the Condition 
        "ENERGY > 500 or ahead[2] < -10 and SIZE > 3", if we were to select the "or" node for removal, the condition
        would become "ENERGY > 500" or "ahead[2] < -10 and SIZE > 3" by promoting the right or left operand. If the
        "and" node had been selected for removal, the condition would become "ENERGY > 500 or ahead[2] < -10" or
        "ENERGY > 500 or SIZE > 3" by randomly promoting the right or left operand.

        A swap is straightforward.

        A replace is also straigtforward.

        A transform simply changes an "and" to an "or" and vice versa.

        An insertion is performed by generating a new LogicalOperator, randomly assignined to be an "and" or an
        "or" randomly assigning the original node to be the right or left child, then randomly selecting another
        node that is a BooleanOperator from somewhere in the AST and inserting it as the other child.
    """

    def logicalOperatorFaultInjector(
        self,
        faultLocus: tuple[LogicalOperator, Rule | LogicalOperator],
        faultType: Mutations | None = None,
    ) -> bool:

        if not faultType:
            faultType = random.choice(
                [
                    Mutations.REMOVE,
                    Mutations.SWAP,
                    Mutations.REPLACE,
                    Mutations.TRANSFORM,
                    Mutations.INSERT,
                ]
            )
        match faultType:
            case Mutations.REMOVE:
                return self.mutateLogicalOperatorRemove(faultLocus)
            case Mutations.SWAP:
                return self.mutateLogicalOperatorSwap(faultLocus)
            case Mutations.REPLACE:
                return self.mutateLogicalOperatorReplace(faultLocus)
            case Mutations.TRANSFORM:
                return self.mutateLogicalOperatorTransform(faultLocus)
            case Mutations.INSERT:
                return self.mutateLogicalOperatorInsert(faultLocus)
            case _:
                raise RuntimeError(
                    f"{faultType} for logicalOperatorFaultInjector() not implemented."
                )

        return False

    def mutateLogicalOperatorRemove(
        self, faultLocus: tuple[LogicalOperator, Rule | LogicalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        side = random.choice([Side.LEFT, Side.RIGHT])
        if side == Side.LEFT:
            parentNode.replaceChild(originalNode, originalNode.leftOperand)
        elif side == Side.RIGHT:
            parentNode.replaceChild(originalNode, originalNode.rightOperand)
        else:
            raise RuntimeError(
                f"{side} is not valid for mutateLogicalOperatorRemove() in {self}."
            )
        return True

    def mutateLogicalOperatorSwap(
        self, faultLocus: tuple[LogicalOperator, Rule | LogicalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        originalNode.swapChildren()
        return True

    def mutateLogicalOperatorReplace(
        self, faultLocus: tuple[LogicalOperator, Rule | LogicalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        candidates = [
            selection
            for selection in self.ast.getNodesByType(LogicalOperator)
            if selection is not originalNode
        ]
        if not candidates:
            # No valid cadidates for the replacement
            return False
        target = cast(LogicalOperator, random.choice(candidates).copyNode())
        parentNode.replaceChild(originalNode, target)
        return True

    def mutateLogicalOperatorTransform(
        self, faultLocus: tuple[LogicalOperator, Rule | LogicalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        originalNode.transformOperator()
        return True

    def mutateLogicalOperatorInsert(
        self, faultLocus: tuple[LogicalOperator, Rule | LogicalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        operatorType = random.choice([TOKENS.T_AND, TOKENS.T_OR])
        operator = TokenLexeme(operatorType, (self.operatorMap.get(operatorType)) or "")
        side = random.choice([Side.LEFT, Side.RIGHT])
        candidates = [
            selection
            for selection in self.ast.getNodesByType(LogicalOperator)
            if selection is not originalNode
        ]
        if not candidates:
            # There were no valid candidates for the other side of the operator.
            return False
        otherOperand = cast(LogicalOperator, random.choice(candidates).copyNode())
        if side == Side.LEFT:
            mutation = LogicalOperator(originalNode, operator, otherOperand)
        elif side == Side.RIGHT:
            mutation = LogicalOperator(otherOperand, operator, originalNode)
        else:
            raise RuntimeError(
                f"No valid side in mutateLogicalOperatorInsert() for {self}."
            )
        parentNode.replaceChild(originalNode, mutation)
        return True

    """
        </LOGICAL_OPERATOR>
    """

    """
        <RELATIONAL_OPERATOR>

        There are 5 valid mutations for <RelationalOperators> - Swap, Replace, Transform, Insert.
    """

    def relationalOperatorFaultInjector(
        self, faultLocus: tuple[RelationalOperator, LogicalOperator | Rule]
    ) -> bool:

        choice = random.choice(
            [
                Mutations.SWAP,
                Mutations.REPLACE,
                Mutations.TRANSFORM,
                Mutations.INSERT,
            ]
        )
        match choice:
            case Mutations.SWAP:
                return self.mutateRelationalOperatorSwap(faultLocus)
            case Mutations.REPLACE:
                return self.mutateRelationalOperatorReplace(faultLocus)
            case Mutations.TRANSFORM:
                return self.mutateRelationalOperatorTransform(faultLocus)
            case Mutations.INSERT:
                return self.mutateRelationalOperatorInsert(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for relationOperationFaultInjector() not implemented."
                )

    def mutateRelationalOperatorSwap(
        self, faultLocus: tuple[RelationalOperator, LogicalOperator | Rule]
    ) -> bool:
        originalNode = faultLocus[0]
        originalNode.swapChildren()
        return True

    def mutateRelationalOperatorReplace(
        self, faultLocus: tuple[RelationalOperator, LogicalOperator | Rule]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        candidates = [
            selection
            for selection in self.ast.getNodesByType(BooleanOperator)
            if selection is not originalNode
        ]
        if not candidates:
            # No valid cadidates for the replacement
            return False
        target = cast(BooleanOperator, random.choice(candidates).copyNode())
        parentNode.replaceChild(originalNode, target)
        return True

    def mutateRelationalOperatorTransform(
        self, faultLocus: tuple[RelationalOperator, LogicalOperator | Rule]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        candidates = list(SET_RELOPS)
        if originalNode.operator.tokenType in candidates:
            candidates.remove(originalNode.operator.tokenType)
        target = random.choice(candidates)
        lexeme = self.operatorMap.get(target)
        if not lexeme:
            raise RuntimeError(f"Failed to get lexeme for {target}.")
        originalNode.transformOperator(TokenLexeme(target, lexeme))
        return True

    def mutateRelationalOperatorInsert(
        self, faultLocus: tuple[RelationalOperator, LogicalOperator | Rule]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        operators = [
            TOKENS.T_AND,
            TOKENS.T_OR,
        ]
        token = random.choice(operators)
        lexeme = self.operatorMap.get(token)
        if not lexeme:
            raise RuntimeError(f"Failed to get lexeme for {token}.")
        operator = TokenLexeme(token, lexeme)
        candidates = [
            selection
            for selection in self.ast.getNodesByType(BooleanOperator)
            if selection is not originalNode
        ]
        if not candidates:
            # No valid cadidates for the replacement
            return False

        otherOperand = cast(BooleanOperator, random.choice(candidates).copyNode())

        side = random.choice([Side.LEFT, Side.RIGHT])
        if side == Side.LEFT:
            mutation = LogicalOperator(originalNode, operator, otherOperand)
        elif side == Side.RIGHT:
            mutation = LogicalOperator(otherOperand, operator, originalNode)
        else:
            raise RuntimeError(f"Bad side: {side} in mutateRelationalOperatorInsert().")

        parentNode.replaceChild(originalNode, mutation)
        return True

    """
        </RELATIONAL_OPERATOR>
    """

    """
        <BINARY_OPERATOR>

        There are 5 valid mutations for a <BinaryOperator> node - Remove, Swap, Replace, Transform, and Insert.

        Remove - Promote the left or right operand to the take this nodes place as the child of the grandparent.

        Swap - Swap left and right operands.

        Replace - Any node of type ExpressionNode is randomly selected and copied to take this node's place.

        Transform - Change the operator to a different operator.

        Insert - Create an ExpressionNode and put this node as one of the children. If you need another child, copy a random ExpressionNode.
    """

    def binaryOperatorFaultInjector(
        self, faultLocus: tuple[BinaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:

        choice = random.choice(
            [
                Mutations.REMOVE,
                Mutations.SWAP,
                Mutations.REPLACE,
                Mutations.TRANSFORM,
                Mutations.INSERT,
            ]
        )
        match choice:
            case Mutations.REMOVE:
                return self.mutateBinaryOperatorRemove(faultLocus)
            case Mutations.SWAP:
                return self.mutateBinaryOperatorSwap(faultLocus)
            case Mutations.REPLACE:
                return self.mutateBinaryOperatorReplace(faultLocus)
            case Mutations.TRANSFORM:
                return self.mutateBinaryOperatorTransform(faultLocus)
            case Mutations.INSERT:
                return self.mutateBinaryOperatorInsert(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for binaryOperationFaultInjector() not implimented."
                )

    def mutateBinaryOperatorRemove(
        self, faultLocus: tuple[BinaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = random.choice([Side.LEFT, Side.RIGHT])
        match choice:
            case Side.LEFT:
                parentNode.replaceChild(originalNode, originalNode.leftOperand)
            case Side.RIGHT:
                parentNode.replaceChild(originalNode, originalNode.rightOperand)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for mutateRemoveBinaryOperator() not implimented."
                )
        return True

    def mutateBinaryOperatorSwap(
        self, faultLocus: tuple[BinaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:
        if not self.ast.rootNode:
            raise RuntimeError("AST was not setup in init for Mutator")
        originalNode = faultLocus[0]
        originalNode.swapChildren()
        return True

    def mutateBinaryOperatorReplace(
        self, faultLocus: tuple[BinaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        candidates = [
            n for n in self.ast.getNodesByType(ExpressionNode) if n is not originalNode
        ]
        if not candidates:
            # Nothing viable to copy.
            return False
        mutation = random.choice(candidates).copyNode()
        parentNode.replaceChild(originalNode, mutation)
        return True

    def mutateBinaryOperatorTransform(
        self, faultLocus: tuple[BinaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:
        originalNode = faultLocus[0]

        choices = ["+", "-", "*", "/", "mod"]
        choices.remove(originalNode.operator.lexeme)
        choice = random.choice(choices)
        originalNode.transformOperator(choice)
        return True

    def mutateBinaryOperatorInsert(
        self, faultLocus: tuple[BinaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        nodeTypeCandidates = [
            "BinaryOperator",
            "UnaryOperator",
            "MemNode",
            "DirectedSensorNode",
        ]
        nodeType = random.choice(nodeTypeCandidates)
        match nodeType:
            case "BinaryOperator":
                opTypeCandidates = list(SET_MULOPS | SET_ADDOPS)
                opType = random.choice(opTypeCandidates)
                if not opType:
                    raise RuntimeError(f"Failed to get opType for {opTypeCandidates}.")
                lexeme = self.operatorMap.get(opType)
                if not lexeme:
                    raise RuntimeError(f"Failed to get opType for {opTypeCandidates}.")
                op = TokenLexeme(opType, lexeme)
                otherOperand = random.choice(
                    [
                        expression
                        for expression in self.ast.getNodesByType(ExpressionNode)
                        if expression is not originalNode
                    ]
                )
                if not otherOperand:
                    return False
                otherOperand = cast(ExpressionNode, otherOperand.copyNode())
                side = random.choice([Side.LEFT, Side.RIGHT])
                match side:
                    case Side.LEFT:
                        mutation = BinaryOperator(originalNode, op, otherOperand)
                    case Side.RIGHT:
                        mutation = BinaryOperator(otherOperand, op, originalNode)
                    case _:
                        raise RuntimeError(f"Failed to match side for {side}.")
            case "UnaryOperator":
                mutation = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), originalNode)
            case "MemNode":
                mutation = MemNode(originalNode)
            case "DirectedSensorNode":
                sensorTypeCandidates = [
                    "nearby",
                    "ahead",
                    "random",
                ]
                sensorType = random.choice(sensorTypeCandidates)
                match sensorType:
                    case "nearby":
                        mutation = DirectedSensorNode(
                            Token(TOKENS.T_NEARBY, "nearby", 0, 0), originalNode
                        )
                    case "ahead":
                        mutation = DirectedSensorNode(
                            Token(TOKENS.T_AHEAD, "ahead", 0, 0), originalNode
                        )
                    case "random":
                        mutation = DirectedSensorNode(
                            Token(TOKENS.T_RANDOM, "random", 0, 0), originalNode
                        )
                    case _:
                        raise RuntimeError(
                            f"Failed to match sensorType for {sensorType}."
                        )
            case _:
                raise NotImplementedError(
                    f"Choice {nodeType} for mutateBinaryOperatorInsert() nodeType is not implemented."
                )
        parentNode.replaceChild(originalNode, mutation)
        return True

    """
        </BINARY_OPERATOR>
    """

    """
        <UNARY_OPERATOR>

        There are 3 valid mutations for a <UnaryOperator> - Remove, Replace, and Insert.
    """

    def unaryOperatorFaultInjector(
        self, faultLocus: tuple[UnaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:
        choice = random.choice(
            [
                Mutations.REMOVE,
                Mutations.REPLACE,
                Mutations.INSERT,
            ]
        )
        match choice:
            case Mutations.REMOVE:
                return self.mutateUnaryOperatorRemove(faultLocus)
            case Mutations.REPLACE:
                return self.mutateUnaryOperatorReplace(faultLocus)
            case Mutations.INSERT:
                return self.mutateUnaryOperatorInsert(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for unaryOperatorFaultInjector() nodeType is not implemented."
                )
        return True

    def mutateUnaryOperatorRemove(
        self, faultLocus: tuple[UnaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        parentNode.replaceChild(originalNode, originalNode.operand)
        return True

    def mutateUnaryOperatorReplace(
        self, faultLocus: tuple[UnaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        candidates = [
            expression
            for expression in self.ast.getNodesByType(ExpressionNode)
            if expression is not originalNode
        ]
        if not candidates:
            return False
        mutation = cast(ExpressionNode, random.choice(candidates).copyNode())
        parentNode.replaceChild(originalNode, mutation)
        return True

    def mutateUnaryOperatorInsert(
        self, faultLocus: tuple[UnaryOperator, ExpressionNode | RelationalOperator]
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        nodeTypeCandidates = [
            "BinaryOperator",
            "UnaryOperator",
            "MemNode",
            "DirectedSensorNode",
        ]
        nodeType = random.choice(nodeTypeCandidates)
        match nodeType:
            case "BinaryOperator":
                opTypeCandidates = list(SET_MULOPS | SET_ADDOPS)
                opType = random.choice(opTypeCandidates)
                if not opType:
                    raise RuntimeError(f"Failed to get opType for {opTypeCandidates}.")
                lexeme = self.operatorMap.get(opType)
                if not lexeme:
                    raise RuntimeError(f"Failed to get opType for {opTypeCandidates}.")
                op = TokenLexeme(opType, lexeme)
                otherOperand = random.choice(
                    [
                        expression
                        for expression in self.ast.getNodesByType(ExpressionNode)
                        if expression is not originalNode
                    ]
                )
                if not otherOperand:
                    return False
                otherOperand = cast(ExpressionNode, otherOperand.copyNode())
                side = random.choice([Side.LEFT, Side.RIGHT])
                match side:
                    case Side.LEFT:
                        mutation = BinaryOperator(originalNode, op, otherOperand)
                    case Side.RIGHT:
                        mutation = BinaryOperator(otherOperand, op, originalNode)
                    case _:
                        raise RuntimeError(f"Failed to match side for {side}.")
            case "UnaryOperator":
                mutation = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), originalNode)
            case "MemNode":
                mutation = MemNode(originalNode)
            case "DirectedSensorNode":
                sensorTypeCandidates = [
                    "nearby",
                    "ahead",
                    "random",
                ]
                sensorType = random.choice(sensorTypeCandidates)
                match sensorType:
                    case "nearby":
                        mutation = DirectedSensorNode(
                            Token(TOKENS.T_NEARBY, "nearby", 0, 0), originalNode
                        )
                    case "ahead":
                        mutation = DirectedSensorNode(
                            Token(TOKENS.T_AHEAD, "ahead", 0, 0), originalNode
                        )
                    case "random":
                        mutation = DirectedSensorNode(
                            Token(TOKENS.T_RANDOM, "random", 0, 0), originalNode
                        )
                    case _:
                        raise RuntimeError(
                            f"Failed to match sensorType for {sensorType}."
                        )
            case _:
                raise NotImplementedError(
                    f"Choice {nodeType} for mutateBinaryOperatorInsert() nodeType is not implemented."
                )
        parentNode.replaceChild(originalNode, mutation)
        return True

    """
        </UNARY_OPERATOR>
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
        i.e. we don't just add to the value. This could change in the future but probably not.
        The transformation of a <Number> node may result in structural changes to the AST. If a
        positive number becomes negative, a <UnaryOperato> is created to be the parent of the new
        value and it replaces the original <Number> in the parent's subtree. Previously, I was collapsing
        double negatives into just a number and removing UnaryOperators with an operand of 0, replacing
        them with just a Number. This is no longer the case, watch out for stale comments.

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
        self, faultLocus: tuple[Number, ASTNode], faultType: Mutations | None = None
    ) -> bool:
        if faultType:
            choice = faultType
        else:
            choice = random.choice(
                [Mutations.REPLACE, Mutations.TRANSFORM, Mutations.INSERT]
            )
        match choice:
            case Mutations.REPLACE:
                return self.mutateNumberReplace(faultLocus)
            case Mutations.TRANSFORM:
                return self.mutateNumberTransform(faultLocus)
            case Mutations.INSERT:
                return self.mutateNumberInsert(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for numberFaultInjector() not implemented."
                )

    def mutateNumberReplace(
        self,
        faultLocus: tuple[Number, ASTNode],
        mutation: ExpressionNode | None = None,
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        # The selected Number node will be replaced a copy of a randomly selected ExpressionNode from elsewhere in the AST.
        # This mutator will also accept an ExpressionNode to be used for the mutation. This is primarily for use by the unit tests.
        mutation = (
            random.choice(
                [
                    n
                    for n in self.ast.getNodesByType(ExpressionNode)
                    if n is not originalNode
                ]
            )
            if not mutation
            else mutation
        )
        mutation = cast(ExpressionNode, mutation.copyNode())
        mutation.ast = parentNode.ast
        # Replace the original child of the parent with the mutation.
        parentNode.replaceChild(originalNode, mutation)
        return True

    def mutateNumberTransform(
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

    def mutateNumberInsert(
        self, faultLocus: tuple[Number, ASTNode], insertType: NodeType | None = None
    ) -> bool:

        originalNode = faultLocus[0]
        parentNode = faultLocus[1]
        choice = (
            random.choice(
                [
                    NodeType.UNARY_OPERATOR,
                    NodeType.BINARY_OPERATOR,
                    NodeType.MEMNODE,
                    NodeType.DIRECTED_SENSOR_NODE,
                ]
            )
            if not insertType
            else insertType
        )
        match choice:
            case NodeType.UNARY_OPERATOR:
                mutation = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), originalNode)
            case NodeType.BINARY_OPERATOR:
                opChoice = random.choice(
                    [
                        TOKENS.T_MINUS,
                        TOKENS.T_STAR,
                        TOKENS.T_DIV,
                        TOKENS.T_PLUS,
                        TOKENS.T_MOD,
                    ]
                )
                side = random.choice([Side.LEFT, Side.RIGHT])
                opLexeme = Mutator.operatorMap.get(opChoice) or ""
                if not opLexeme:
                    raise RuntimeError(
                        f"Failed to get opLexeme in mutateInsertNumber() for choice 'BinaryOperator'."
                    )

                candidates = [
                    n
                    for n in self.ast.getNodesByType(ExpressionNode)
                    if n is not originalNode
                ]
                if not candidates:
                    # There was no valid candidate to select
                    return False
                otherExpression = cast(
                    ExpressionNode, random.choice(candidates).copyNode()
                )

                if side == Side.LEFT:
                    mutation = BinaryOperator(
                        originalNode, TokenLexeme(opChoice, opLexeme), otherExpression
                    )
                else:
                    mutation = BinaryOperator(
                        otherExpression, TokenLexeme(opChoice, opLexeme), originalNode
                    )
            case NodeType.MEMNODE | NodeType.DIRECTED_SENSOR_NODE:
                node_choice = random.choice(
                    [TOKENS.T_MEM, TOKENS.T_AHEAD, TOKENS.T_NEARBY, TOKENS.T_RANDOM]
                )
                if node_choice == TOKENS.T_MEM:
                    mutation = MemNode(originalNode)
                else:
                    lexeme = Mutator.operatorMap.get(node_choice) or ""
                    if not lexeme:
                        raise RuntimeError(
                            f"Failed to get lexeme in mutateInsertNumber() for choice 'MemNodeOrDirectedSensorNode'."
                        )
                    mutation = DirectedSensorNode(
                        Token(node_choice, lexeme, 0, 0), originalNode
                    )
            case _:
                raise RuntimeError(
                    f"Invalid insertType {choice} for mutateInsertNumber()."
                )

        parentNode.replaceChild(originalNode, mutation)
        return True

    """
        </NUMBER>
    """

    """
        <MEMNODE>

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
        faultType: Mutations | None = None,
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        choice = (
            faultType
            if faultType is not None
            else random.choice([Mutations.REPLACE, Mutations.INSERT])
        )
        match choice:
            case Mutations.REPLACE:
                return self.mutateMemNodeReplace(faultLocus)
            case Mutations.INSERT:
                return self.mutateMemNodeInsert(faultLocus)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for memNodeFaultInjector() not implemented."
                )

    def mutateMemNodeReplace(
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
                candidates = [
                    n for n in self.ast.getNodesByType(MemNode) if n is not originalNode
                ]
                mutation = random.choice(candidates)
            mutation = cast(MemNode, mutation.copyNode())
        else:
            # If the parent is not an Update destination, the MemNode is part of an Expression
            # and can be replaced by any ExpressionNode
            if mutation is None:
                candidates = [
                    n
                    for n in self.ast.getNodesByType(ExpressionNode)
                    if n is not originalNode
                ]
                mutation = random.choice(candidates)
            mutation = cast(ExpressionNode, mutation.copyNode())
        parentNode.replaceChild(originalNode, mutation)
        return True

    def mutateMemNodeInsert(
        self, faultLocus: tuple[MemNode, ASTNode], insertType: NodeType | None = None
    ) -> bool:
        originalNode = faultLocus[0]
        parentNode = faultLocus[1]

        # If the MemNode is an Update destination, the only valid structural insertion is another MemNode
        if isinstance(parentNode, Update) and originalNode is parentNode.destination:
            choice = NodeType.MEMNODE
        else:
            choice = (
                insertType
                if insertType is not None
                else random.choice(
                    [
                        NodeType.UNARY_OPERATOR,
                        NodeType.BINARY_OPERATOR,
                        NodeType.DIRECTED_SENSOR_NODE,
                        NodeType.MEMNODE,
                    ]
                )
            )
        match choice:
            case NodeType.UNARY_OPERATOR:
                mutation = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), originalNode)
            case NodeType.BINARY_OPERATOR:
                opChoice = random.choice(
                    [
                        TOKENS.T_MINUS,
                        TOKENS.T_STAR,
                        TOKENS.T_DIV,
                        TOKENS.T_PLUS,
                        TOKENS.T_MOD,
                    ]
                )

                opLexeme = Mutator.operatorMap.get(opChoice)
                if not opLexeme:
                    raise RuntimeError(
                        f"Failed to get lexeme for {opChoice} in mutateInsertMemNode()."
                    )
                candidates = [
                    n
                    for n in self.ast.getNodesByType(ExpressionNode)
                    if n is not originalNode
                ]
                if not candidates:
                    # There was no valid candidate to select
                    return False
                otherExpression = cast(
                    ExpressionNode, random.choice(candidates).copyNode()
                )
                side = random.choice([Side.LEFT, Side.RIGHT])
                if side == Side.LEFT:
                    mutation = BinaryOperator(
                        originalNode, TokenLexeme(opChoice, opLexeme), otherExpression
                    )
                else:
                    mutation = BinaryOperator(
                        otherExpression, TokenLexeme(opChoice, opLexeme), originalNode
                    )
            case NodeType.DIRECTED_SENSOR_NODE:
                sensorChoice = random.choice(
                    [TOKENS.T_AHEAD, TOKENS.T_NEARBY, TOKENS.T_RANDOM]
                )
                lexeme = Mutator.operatorMap.get(sensorChoice) or ""
                token = Token(sensorChoice, lexeme, 0, 0)
                mutation = DirectedSensorNode(token, originalNode)
            case NodeType.MEMNODE:
                mutation = MemNode(originalNode)
            case _:
                raise NotImplementedError(
                    f"Choice {choice} for mutateMemNodeInsert() not implemented."
                )

        parentNode.replaceChild(originalNode, mutation)
        return True

    """
        </MEMNODE>
    """

    """
        <SENSOR>
    """

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
        </SENSOR>
    """
