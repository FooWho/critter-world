from __future__ import annotations
import unittest
from lexer import Lexer
from parser import Parser
from schemas import TOKENS, CritterParseError, TokenLexeme, Token
from typing import cast, LiteralString
from abstractSyntaxTree import (
    AbstractSyntaxTree,
    Program,
    MemNode,
    SensorNode,
    SmellNode,
    DirectedSensorNode,
    Number,
    RelationalOperator,
    BooleanOperator,
    LogicalOperator,
    BinaryOperator,
    UnaryOperator,
    Update,
    Action,
    ServeAction,
    ExpressionNode,
    Rule,
    countNodes,
)
from mutator import Mutator, NodeType
from schemas import SET_RELOPS
import random


class TestMutator(unittest.TestCase):

    def setUp(self):
        with open("test/critter1.crtr", "r", encoding="utf-8") as file:
            lines = file.readlines()
        lineContent = lines[8:]
        content = "".join(lineContent)
        self.lexer = Lexer()
        tokens = self.lexer.tokenize(content)
        self.parser = Parser(tokens)
        self.astCritter1 = AbstractSyntaxTree(self.parser.parse())

        with open("test/critter2.crtr", "r", encoding="utf-8") as file:
            lines = file.readlines()
        lineContent = lines[8:]
        content = "".join(lineContent)
        tokens = self.lexer.tokenize(content)
        self.parser = Parser(tokens)
        self.astCritter2 = AbstractSyntaxTree(self.parser.parse())

        with open("test/critter3.crtr", "r", encoding="utf-8") as file:
            lines = file.readlines()
        lineContent = lines[8:]
        content = "".join(lineContent)
        tokens = self.lexer.tokenize(content)
        self.parser = Parser(tokens)
        self.astCritter3 = AbstractSyntaxTree(self.parser.parse())

        with open("test/critter4.crtr", "r", encoding="utf-8") as file:
            lines = file.readlines()
        lineContent = lines[8:]
        content = "".join(lineContent)
        tokens = self.lexer.tokenize(content)
        self.parser = Parser(tokens)
        self.astCritter4 = AbstractSyntaxTree(self.parser.parse())

    def createProgram(self, programString: str) -> Program:
        parser = Parser(Lexer().tokenize(programString))
        program = parser.parse()
        return program

    def testGenerateFaultLocus(self):
        mutator = Mutator(self.astCritter1)
        for i in range(0, 5):
            faultLocus = mutator.generateFaultLocus()
            childNode = faultLocus[0]
            parentNode = faultLocus[1]
            if isinstance(childNode, Program) and isinstance(
                parentNode, AbstractSyntaxTree
            ):
                self.assertTrue(parentNode is childNode.ast)
            else:
                self.assertTrue(childNode in parentNode)

    def testNumberTransformNegativeToZero(self):
        # Negative to Zero
        # Left operand goes from UnaryOperand(1) to UnaryOperand(0).
        program = self.createProgram("-1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        self.assertEqual(ast.nodeCount, 7)
        condition = cast(RelationalOperator, program.rules[0].condition)
        parentNode = condition.leftOperand
        self.assertIsInstance(parentNode, UnaryOperator)
        self.assertEqual(parentNode.evaluate(), -1)
        parentNode = cast(UnaryOperator, parentNode)
        originalNode = cast(Number, parentNode.operand)
        self.assertEqual(originalNode.value, 1)
        mutator.mutateNumberTransform((originalNode, parentNode), -1)
        self.assertIsInstance(condition.leftOperand, UnaryOperator)
        mutation = cast(UnaryOperator, condition.leftOperand)
        self.assertEqual(mutation.evaluate(), 0)
        self.assertEqual(ast.nodeCount, 7)
        self.assertEqual(str(condition), "-0 < 3")

    def testNumberTransformPositiveToNegative(self):
        # Positive to Negative
        # UnaryNode should get added -- left operand goes from 1 to UnaryOperator(3). 1 + (-4) = UnaryOperator(3)
        # Node cound goes from 6 to 7.
        program = self.createProgram("1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        self.assertEqual(ast.nodeCount, 6)
        self.assertIsInstance(program.rules[0].condition, RelationalOperator)
        parentNode = cast(RelationalOperator, program.rules[0].condition)
        self.assertIsInstance(parentNode.leftOperand, Number)
        originalNode = cast(Number, parentNode.leftOperand)
        self.assertEqual(originalNode.value, originalNode.evaluate())
        self.assertEqual(originalNode.evaluate(), 1)
        mutator.mutateNumberTransform((originalNode, parentNode), -4)
        # Left operand of the condition is no longer originalNode, it's an orphan and the child is a UnaryOperator
        self.assertFalse(
            cast(RelationalOperator, program.rules[0].condition).leftOperand
            is originalNode
        )
        self.assertIsInstance(program.rules[0].condition, RelationalOperator)
        grandparent = cast(RelationalOperator, program.rules[0].condition)
        self.assertIsInstance(grandparent.leftOperand, UnaryOperator)
        parent = cast(UnaryOperator, grandparent.leftOperand)
        self.assertEqual(parent.evaluate(), -3)
        self.assertEqual(ast.nodeCount, 7)

    def testNumberTransformPositiveToPositive(self):
        # Positive to Positive
        program = self.createProgram("1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        self.assertEqual(ast.nodeCount, 6)
        condition = cast(RelationalOperator, program.rules[0].condition)
        parentNode = cast(RelationalOperator, condition)
        originalNode = cast(Number, parentNode.leftOperand)
        mutator.mutateNumberTransform((originalNode, parentNode), 4)  # 1 + 4 = 5
        self.assertIsInstance(condition.leftOperand, Number)
        self.assertEqual(condition.leftOperand.evaluate(), 5)
        self.assertEqual(ast.nodeCount, 6)

    def testNumberTransformNegativeToDoubleNegative(self):
        # Negative to Double Negative
        program = self.createProgram("-2 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        self.assertEqual(ast.nodeCount, 7)
        condition = cast(RelationalOperator, program.rules[0].condition)
        parentNode = cast(UnaryOperator, condition.leftOperand)
        originalNode = cast(Number, parentNode.operand)
        mutator.mutateNumberTransform(
            (originalNode, parentNode), -3
        )  # UnaryOperator(2) + (-3) = UnaryOperator(UnaryOperator(1))
        self.assertIsInstance(condition.leftOperand, UnaryOperator)
        negNode = cast(UnaryOperator, condition.leftOperand)
        self.assertEqual(negNode.evaluate(), 1)
        self.assertIsInstance(negNode.operand, UnaryOperator)
        negNode = cast(UnaryOperator, negNode.operand)
        self.assertEqual(negNode.evaluate(), -1)
        self.assertIsInstance(negNode.operand, Number)
        number = cast(Number, negNode.operand)
        self.assertEqual(number.evaluate(), 1)
        # Node count increased by one because we introduced a new UnaryOperator node.
        self.assertEqual(ast.nodeCount, 8)
        self.assertEqual(str(condition), "--1 < 3")
        self.assertEqual(condition.leftOperand.evaluate(), 1)

    def testNumberInsertUnaryOperator(self):
        program = self.createProgram("1 < 2 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        # Setup faultLocus. originalNode is "1" and the parentNode is "1 < 2".
        condition = cast(RelationalOperator, program.rules[0].condition)
        faultLocus = (
            cast(Number, condition.leftOperand),
            condition,
        )
        self.assertIsInstance(condition.leftOperand, Number)

        # Insert a unary operator as the parent of "1" in the expression "1 < 2".
        # After this mutation, the expression will be "-1 < 2" or, RelationalOperator(UnaryOperator(1),2)
        mutator.mutateNumberInsert(faultLocus, NodeType.UNARY_OPERATOR)
        # Left operand of the condition is now a UnaryOperand instead of a Number
        self.assertIsInstance(condition.leftOperand, UnaryOperator)
        self.assertEqual(str(condition), "-1 < 2")

    def testNumberInsertUnaryOperatorDoubleNegative(self):
        # Set new faultLocus. We are going to insert a UnaryOperator as the parent
        # of the -1 in the expression "-1 < 2". This will create a double negative.
        # The resulting expression will be "--1 < 2"
        program = self.createProgram("-1 < 2 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        self.assertEqual(ast.nodeCount, 7)
        condition = cast(RelationalOperator, program.rules[0].condition)
        faultLocus = (
            cast(Number, cast(UnaryOperator, condition.leftOperand).operand),
            condition.leftOperand,
        )
        # faultLocus is (Number(1), UnaryOperator(Number(1)))
        mutator.mutateNumberInsert(faultLocus, NodeType.UNARY_OPERATOR)
        self.assertIsInstance(condition.leftOperand, UnaryOperator)
        self.assertEqual(str(condition), "--1 < 2")
        self.assertEqual(ast.nodeCount, 8)

    def testNumberInsertBinaryOperator(self):
        # Set a new faultLocus. Insert a BinaryOperator as as the parent of the "2" in "1 < 2"
        program = self.createProgram("1 < 2 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        self.assertEqual(ast.nodeCount, 6)
        condition = cast(RelationalOperator, program.rules[0].condition)
        faultLocus = (cast(Number, condition.rightOperand), condition)
        mutator.mutateNumberInsert(faultLocus, NodeType.BINARY_OPERATOR)
        self.assertIsInstance(condition.rightOperand, BinaryOperator)
        binOp = cast(BinaryOperator, condition.rightOperand)
        self.assertTrue(
            binOp.operator.lexeme == "+"
            or binOp.operator.lexeme == "-"
            or binOp.operator.lexeme == "*"
            or binOp.operator.lexeme == "/"
            or binOp.operator.lexeme == "mod"
        )
        self.assertTrue(
            binOp.leftOperand.evaluate() == 1 or binOp.leftOperand.evaluate() == 2
        )
        self.assertTrue(
            binOp.rightOperand.evaluate() == 1 or binOp.rightOperand.evaluate() == 2
        )
        self.assertEqual(ast.nodeCount, 8)

    def testNumberInsertMemNodeOrDirectedSensorNode(self):
        program = self.createProgram("1 < 2 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        # Set a new faultLocus. Insert a MemNode or DirectedSensorNode (Choice 3)
        condition = cast(RelationalOperator, program.rules[0].condition)
        faultLocus = (cast(Number, condition.leftOperand), condition)
        mutator.mutateNumberInsert(
            faultLocus, random.choice([NodeType.MEMNODE, NodeType.DIRECTED_SENSOR_NODE])
        )
        self.assertTrue(
            isinstance(condition.leftOperand, MemNode)
            or isinstance(condition.leftOperand, DirectedSensorNode)
        )
        newNode = cast(MemNode | DirectedSensorNode, condition.leftOperand)
        self.assertIsInstance(newNode.value, Number)
        self.assertTrue(newNode.value.evaluate() == 1)

    def testNumberReplace(self):
        # Replace the 4 with 2 * 17
        program = self.createProgram("1 + 4 < 2 * 17 mod 12 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        self.assertIsInstance(program.rules[0].condition, RelationalOperator)
        grandparent = cast(RelationalOperator, program.rules[0].condition)
        self.assertIsInstance(grandparent.leftOperand, BinaryOperator)
        binaryOperationNode = cast(BinaryOperator, grandparent.leftOperand)
        originalNode = binaryOperationNode.rightOperand
        self.assertIsInstance(grandparent.rightOperand, BinaryOperator)
        replacementParent = cast(BinaryOperator, grandparent.rightOperand)
        replacementNode = cast(BinaryOperator, replacementParent.leftOperand)
        originalNode = binaryOperationNode.rightOperand

        mutator.mutateNumberReplace(
            (cast(Number, originalNode), binaryOperationNode),
            cast(ExpressionNode, replacementNode),
        )
        self.assertEqual("1 + 2 * 17 < 2 * 17 mod 12", str(program.rules[0].condition))

    def testMemNodeReplaceDestination(self):
        program = self.createProgram("1 = 1 --> mem[0] := 5;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        update = cast(Update, program.rules[0].commands[0])
        originalNode = cast(MemNode, update.destination)

        # We need a new MemNode to replace it with
        replacement = MemNode(Number(value=2))

        mutator.mutateMemNodeReplace((originalNode, update), replacement)

        self.assertIsInstance(update.destination, MemNode)
        update.destination = cast(MemNode, update.destination)
        self.assertEqual(update.destination.value.evaluate(), 2)

    def testMemNodeReplaceFailsIfOnlyOneMemNode(self):
        # Program with exactly one MemNode
        program = self.createProgram("1 = 1 --> mem[0] := 5;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        update = cast(Update, program.rules[0].commands[0])
        originalNode = cast(MemNode, update.destination)

        # Do not pass a replacement node. It should return False because it cannot find another MemNode to swap with.
        result = mutator.mutateMemNodeReplace((originalNode, update))
        self.assertFalse(result)

    def testMemNodeReplaceSource(self):
        program = self.createProgram("1 = 1 --> MEMSIZE := mem[3];")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        update = cast(Update, program.rules[0].commands[0])
        originalNode = cast(MemNode, update.source)

        # Replace it with a Number
        replacement = Number(value=42)
        mutator.mutateMemNodeReplace((originalNode, update), replacement)

        self.assertIsInstance(update.source, Number)
        update.source = cast(Number, update.source)
        self.assertEqual(update.source.evaluate(), 42)

    def testMemNodeInsertUnaryOperator(self):
        program = self.createProgram("1 = mem[0] --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        originalNode = cast(MemNode, condition.rightOperand)

        mutator.mutateMemNodeInsert((originalNode, condition), NodeType.UNARY_OPERATOR)
        self.assertIsInstance(condition.rightOperand, UnaryOperator)
        unary = cast(UnaryOperator, condition.rightOperand)
        self.assertIsInstance(unary.operand, MemNode)

    def testMemNodeInsertBinaryOperator(self):
        program = self.createProgram("1 = mem[0] --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        originalNode = cast(MemNode, condition.rightOperand)

        mutator.mutateMemNodeInsert((originalNode, condition), NodeType.BINARY_OPERATOR)
        self.assertIsInstance(condition.rightOperand, BinaryOperator)

    def testMemNodeInsertDirectedSensorNode(self):
        program = self.createProgram("1 = mem[0] --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        originalNode = cast(MemNode, condition.rightOperand)

        mutator.mutateMemNodeInsert(
            (originalNode, condition), NodeType.DIRECTED_SENSOR_NODE
        )
        self.assertIsInstance(condition.rightOperand, DirectedSensorNode)

    def testMemNodeInsertMemNode(self):
        program = self.createProgram("1 = mem[0] --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        originalNode = cast(MemNode, condition.rightOperand)

        # Insert a MemNode wrapper (Choice 3)
        mutator.mutateMemNodeInsert((originalNode, condition), NodeType.MEMNODE)
        self.assertIsInstance(condition.rightOperand, MemNode)
        outerMem = cast(MemNode, condition.rightOperand)
        self.assertIsInstance(outerMem.value, MemNode)

    def testMemNodeInsertDestination(self):
        # Start with mem[0] := 5
        program = self.createProgram("1 = 1 --> mem[0] := 5;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        update = cast(Update, program.rules[0].commands[0])
        originalNode = cast(MemNode, update.destination)

        # Do an insertion. Because it's a destination, it MUST force choice 3 and wrap it in a MemNode
        mutator.mutateMemNodeInsert((originalNode, update))

        self.assertIsInstance(update.destination, MemNode)
        outerMem = cast(MemNode, update.destination)
        self.assertIsInstance(outerMem.value, MemNode)

    def testRuleRemove(self):
        program = self.createProgram("1 = 1 --> wait; 2 = 2 --> forward;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule1 = program.rules[0]
        rule2 = program.rules[1]

        self.assertEqual(len(program.rules), 2)
        result = mutator.mutateRemoveRule((rule1, program))

        self.assertTrue(result)
        self.assertEqual(len(program.rules), 1)
        self.assertIs(program.rules[0], rule2)

    def testRuleRemoveFailsIfOnlyOne(self):
        program = self.createProgram("1 = 1 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]

        result = mutator.mutateRemoveRule((rule, program))
        self.assertFalse(result)

    def testRuleSwapWithAction(self):
        program = self.createProgram("1 = 1 --> mem[0] := 1 mem[1] := 2 wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        cmd1 = rule.commands[0]
        cmd2 = rule.commands[1]
        action = rule.commands[2]

        result = mutator.mutateSwapRule((rule, program))

        self.assertTrue(result)
        self.assertIs(rule.commands[2], action)  # Action must remain at the end
        self.assertIs(rule.commands[0], cmd2)
        self.assertIs(rule.commands[1], cmd1)

    def testRuleReplace(self):
        program = self.createProgram("1 = 1 --> wait; 2 = 2 --> forward;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule1 = program.rules[0]
        rule2 = program.rules[1]

        result = mutator.mutateReplaceRule((rule1, program))

        self.assertTrue(result)
        self.assertIsNot(program.rules[0], rule1)
        self.assertEqual(str(program.rules[0]), str(rule2))  # Must be a copy of rule2

    def testRuleDuplicateWithAction(self):
        program = self.createProgram("1 = 1 --> mem[0] := 5 wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        target = rule.commands[0]
        result = mutator.mutateDuplicateRule((rule, program), target)

        self.assertTrue(result)
        self.assertEqual(len(rule.commands), 3)
        self.assertIsInstance(rule.commands[0], Update)
        self.assertIsInstance(rule.commands[1], Update)
        self.assertIsInstance(rule.commands[2], Action)

    def testBinaryOperatorRemove(self):
        program = self.createProgram("1 < 5 + 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        binOp = cast(BinaryOperator, condition.rightOperand)
        left = binOp.leftOperand
        right = binOp.rightOperand

        result = mutator.mutateBinaryOperatorRemove((binOp, condition))

        self.assertTrue(result)
        # Condition's right operand should now be either the left (5) or right (3) node of the former BinaryOperator
        self.assertTrue(
            condition.rightOperand is left or condition.rightOperand is right
        )

    def testBinaryOperatorReplace(self):
        program = self.createProgram("1 < 5 + 3 --> mem[0] := 2;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        binOp = cast(BinaryOperator, condition.rightOperand)

        result = mutator.mutateBinaryOperatorReplace((binOp, condition))

        self.assertTrue(result)
        self.assertIsNot(condition.rightOperand, binOp)
        self.assertIsInstance(condition.rightOperand, ExpressionNode)

    def testBinaryOperatorInsert(self):
        program = self.createProgram("1 < 5 + 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        binOp = cast(BinaryOperator, condition.rightOperand)

        result = mutator.mutateBinaryOperatorInsert((binOp, condition))

        self.assertTrue(result)
        self.assertIsNot(condition.rightOperand, binOp)

        # The original binOp must be wrapped by the new node as one of its children
        newNode = condition.rightOperand
        is_child = False
        if isinstance(newNode, UnaryOperator):
            is_child = newNode.operand is binOp
        elif isinstance(newNode, BinaryOperator):
            is_child = newNode.leftOperand is binOp or newNode.rightOperand is binOp
        elif isinstance(newNode, MemNode):
            is_child = newNode.value is binOp
        elif isinstance(newNode, DirectedSensorNode):
            is_child = newNode.value is binOp

        self.assertTrue(is_child)

    def testBinaryOperatorSwap(self):
        program = self.createProgram("1 < 5 - 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        binOp = cast(BinaryOperator, condition.rightOperand)

        left = binOp.leftOperand
        right = binOp.rightOperand

        result = mutator.mutateBinaryOperatorSwap((binOp, condition))

        self.assertTrue(result)
        self.assertIs(binOp.leftOperand, right)
        self.assertIs(binOp.rightOperand, left)
        self.assertEqual(str(binOp), "3 - 5")

    def testBinaryOperatorTransform(self):
        program = self.createProgram("1 < 5 + 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        binOp = cast(BinaryOperator, condition.rightOperand)

        result = mutator.mutateBinaryOperatorTransform((binOp, condition))

        self.assertTrue(result)
        self.assertNotEqual(binOp.operator.lexeme, "+")
        self.assertIn(binOp.operator.lexeme, ["-", "*", "/", "mod"])

    def testUnaryOperatorRemove(self):
        program = self.createProgram("1 < -5 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        unOp = cast(UnaryOperator, condition.rightOperand)
        operand = unOp.operand

        result = mutator.mutateUnaryOperatorRemove((unOp, condition))

        self.assertTrue(result)
        self.assertIs(condition.rightOperand, operand)

    def testUnaryOperatorReplace(self):
        program = self.createProgram("1 < -5 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        unOp = cast(UnaryOperator, condition.rightOperand)

        result = mutator.mutateUnaryOperatorReplace((unOp, condition))

        self.assertTrue(result)
        self.assertIsNot(condition.rightOperand, unOp)
        self.assertIsInstance(condition.rightOperand, ExpressionNode)

    def testUnaryOperatorInsert(self):
        program = self.createProgram("1 < -5 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        unOp = cast(UnaryOperator, condition.rightOperand)

        result = mutator.mutateUnaryOperatorInsert((unOp, condition))

        self.assertTrue(result)
        self.assertIsNot(condition.rightOperand, unOp)

        newNode = condition.rightOperand
        is_child = False
        if isinstance(newNode, UnaryOperator):
            is_child = newNode.operand is unOp
        elif isinstance(newNode, BinaryOperator):
            is_child = newNode.leftOperand is unOp or newNode.rightOperand is unOp
        elif isinstance(newNode, MemNode):
            is_child = newNode.value is unOp
        elif isinstance(newNode, DirectedSensorNode):
            is_child = newNode.value is unOp

        self.assertTrue(is_child)

    def testRelationalOperatorSwap(self):
        program = self.createProgram("1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)

        left = condition.leftOperand
        right = condition.rightOperand

        mutator.mutateRelationalOperatorSwap((condition, program.rules[0]))

        self.assertIs(condition.leftOperand, right)
        self.assertIs(condition.rightOperand, left)
        self.assertEqual(str(condition), "3 < 1")

    def testRelationalOperatorReplace(self):
        program = self.createProgram("1 < 3 or 4 = 4 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        rootOp = cast(LogicalOperator, rule.condition)
        relOp = cast(RelationalOperator, rootOp.leftOperand)

        result = mutator.mutateRelationalOperatorReplace((relOp, rootOp))
        self.assertTrue(result)
        self.assertIsNot(rootOp.leftOperand, relOp)
        self.assertIsInstance(rootOp.leftOperand, BooleanOperator)

    def testRelationalOperatorTransform(self):
        program = self.createProgram("1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)

        self.assertEqual(condition.operator.tokenType, TOKENS.T_LESS)

        result = mutator.mutateRelationalOperatorTransform(
            (condition, program.rules[0])
        )
        self.assertTrue(result)
        self.assertNotEqual(condition.operator.tokenType, TOKENS.T_LESS)
        self.assertIn(condition.operator.tokenType, SET_RELOPS)

    def testRelationalOperatorInsert(self):
        program = self.createProgram("1 < 3 or 4 = 4 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        rootOp = cast(LogicalOperator, rule.condition)
        relOp = cast(RelationalOperator, rootOp.leftOperand)

        result = mutator.mutateRelationalOperatorInsert((relOp, rootOp))
        self.assertTrue(result)
        self.assertIsInstance(rootOp.leftOperand, LogicalOperator)
        newLogical = cast(LogicalOperator, rootOp.leftOperand)
        self.assertTrue(
            newLogical.leftOperand is relOp or newLogical.rightOperand is relOp
        )

    def testLogicalOperatorRemove(self):
        program = self.createProgram("1 < 2 and 3 < 4 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        condition = cast(LogicalOperator, rule.condition)

        left = condition.leftOperand
        right = condition.rightOperand

        result = mutator.mutateLogicalOperatorRemove((condition, rule))

        self.assertTrue(result)
        self.assertTrue(rule.condition is left or rule.condition is right)
        self.assertNotIsInstance(rule.condition, LogicalOperator)

    def testLogicalOperatorRemoveNested(self):
        program = self.createProgram("1 < 2 and 3 < 4 or 5 < 6 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]

        rootOp = cast(LogicalOperator, rule.condition)
        nestedOp = cast(LogicalOperator, rootOp.leftOperand)

        left = nestedOp.leftOperand
        right = nestedOp.rightOperand

        result = mutator.mutateLogicalOperatorRemove((nestedOp, rootOp))

        self.assertTrue(result)
        self.assertTrue(rootOp.leftOperand is left or rootOp.leftOperand is right)

    def testLogicalOperatorSwap(self):
        program = self.createProgram("1 < 2 and 3 < 4 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        condition = cast(LogicalOperator, rule.condition)

        left = condition.leftOperand
        right = condition.rightOperand

        result = mutator.mutateLogicalOperatorSwap((condition, rule))

        self.assertTrue(result)
        self.assertIs(condition.leftOperand, right)
        self.assertIs(condition.rightOperand, left)
        self.assertEqual(str(condition), "3 < 4 and 1 < 2")

    def testLogicalOperatorReplace(self):
        program = self.createProgram("1 < 2 and 3 < 4 or 5 < 6 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]

        rootOp = cast(LogicalOperator, rule.condition)
        nestedOp = cast(LogicalOperator, rootOp.leftOperand)

        result = mutator.mutateLogicalOperatorReplace((nestedOp, rootOp))

        self.assertTrue(result)
        self.assertIsNot(rootOp.leftOperand, rootOp)
        self.assertIsInstance(rootOp.leftOperand, LogicalOperator)
        replacedOp = cast(LogicalOperator, rootOp.leftOperand)
        # Should be a copy of rootOp
        self.assertEqual(replacedOp.operator.tokenType, TOKENS.T_OR)

    def testLogicalOperatorReplaceFailsIfOnlyOne(self):
        program = self.createProgram("1 < 2 and 3 < 4 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        condition = cast(LogicalOperator, rule.condition)

        result = mutator.mutateLogicalOperatorReplace((condition, rule))
        self.assertFalse(result)

    def testLogicalOperatorTransform(self):
        program = self.createProgram("1 < 2 and 3 < 4 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        condition = cast(LogicalOperator, rule.condition)

        self.assertEqual(condition.operator.tokenType, TOKENS.T_AND)

        result = mutator.mutateLogicalOperatorTransform((condition, rule))

        self.assertTrue(result)
        self.assertEqual(condition.operator.tokenType, TOKENS.T_OR)
        self.assertEqual(condition.operator.lexeme, "or")

    def testLogicalOperatorInsert(self):
        program = self.createProgram("1 < 2 and 3 < 4 or 5 < 6 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]

        rootOp = cast(LogicalOperator, rule.condition)
        nestedOp = cast(LogicalOperator, rootOp.leftOperand)

        result = mutator.mutateLogicalOperatorInsert((nestedOp, rootOp))
        self.assertTrue(result)
        self.assertIsInstance(rootOp.leftOperand, LogicalOperator)
        insertedOp = cast(LogicalOperator, rootOp.leftOperand)
        self.assertTrue(
            insertedOp.leftOperand is nestedOp or insertedOp.rightOperand is nestedOp
        )

    def testProgramReplaceChild(self):
        program = self.createProgram("1 = 1 --> wait;")
        ast = AbstractSyntaxTree(program)

        initialNodeCount = ast.nodeCount
        oldRule = program.rules[0]

        newCondition = RelationalOperator(
            BinaryOperator(
                Number(value=1), TokenLexeme(TOKENS.T_PLUS, "+"), Number(value=2)
            ),
            TokenLexeme(TOKENS.T_EQU, "="),
            Number(value=3),
        )
        newRule = Rule(newCondition, [Action(Token(TOKENS.T_WAIT, "wait", 0, 0))])

        program.replaceChild(oldRule, newRule)

        self.assertIs(program.rules[0], newRule)
        self.assertIsNot(program.rules[0], oldRule)
        # oldRule had 5 nodes, newRule has 7, diff is +2
        self.assertEqual(ast.nodeCount, initialNodeCount + 2)

    def testRuleReplaceChild(self):
        program = self.createProgram("1 = 1 --> wait;")
        ast = AbstractSyntaxTree(program)

        rule = program.rules[0]
        oldCommand = rule.commands[0]

        newCommand = Action(Token(TOKENS.T_EAT, "eat", 0, 0))

        rule.replaceChild(oldCommand, newCommand)
        self.assertIs(rule.commands[0], newCommand)
        self.assertEqual(str(newCommand), "eat")

        missingCommand = Action(Token(TOKENS.T_BUD, "bud", 0, 0))
        with self.assertRaises(RuntimeError):
            rule.replaceChild(missingCommand, newCommand)

    def testUnaryOperatorReplaceChildDoubleNegative(self):
        # Replacing the child of a UnaryOperator with another UnaryOperator should result in a double negative.
        program = self.createProgram("-1 = -1 --> wait;")
        ast = AbstractSyntaxTree(program)
        condition = cast(RelationalOperator, program.rules[0].condition)
        unaryOp = cast(UnaryOperator, condition.leftOperand)

        newChild = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), Number(value=5))
        unaryOp.replaceChild(unaryOp.operand, newChild)

        # There should be a double negative and it should evaluate to a positive number.
        self.assertIsInstance(condition.leftOperand, UnaryOperator)
        unaryOp = cast(UnaryOperator, condition.leftOperand)
        self.assertIsInstance(unaryOp.operand, UnaryOperator)
        child = cast(UnaryOperator, unaryOp.operand)
        self.assertEqual(str(unaryOp), "--5")
        self.assertEqual(unaryOp.evaluate(), 5)
        self.assertEqual(str(child), "-5")
        self.assertEqual(child.evaluate(), -5)

    def testUpdateRemove(self):
        program = self.createProgram("1 = 1 --> mem[0] := 1 wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        update = cast(Update, rule.commands[0])
        action = rule.commands[1]

        self.assertEqual(len(rule.commands), 2)
        result = mutator.mutateUpdateRemove((update, rule))

        self.assertTrue(result)
        self.assertEqual(len(rule.commands), 1)
        self.assertIs(rule.commands[0], action)

    def testUpdateRemoveFailsIfOnlyCommand(self):
        program = self.createProgram("1 = 1 --> mem[0] := 1;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        update = cast(Update, rule.commands[0])

        self.assertEqual(len(rule.commands), 1)
        result = mutator.mutateUpdateRemove((update, rule))

        self.assertFalse(result)
        self.assertEqual(len(rule.commands), 1)
        self.assertIs(rule.commands[0], update)

    def testUpdateSwap(self):
        program = self.createProgram("1 = 1 --> mem[0] := mem[1];")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        update = cast(Update, rule.commands[0])

        result = mutator.mutateUpdateSwap((update, rule))

        self.assertTrue(result)
        self.assertIsInstance(update.destination, MemNode)
        self.assertIsInstance(update.source, MemNode)
        dest = cast(MemNode, update.destination)
        src = cast(MemNode, update.source)
        self.assertEqual(dest.value.evaluate(), 1)
        self.assertEqual(src.value.evaluate(), 0)

    def testUpdateSwapFailsIfNotBothMemNodes(self):
        program = self.createProgram("1 = 1 --> mem[0] := 5;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        update = cast(Update, rule.commands[0])

        result = mutator.mutateUpdateSwap((update, rule))

        self.assertFalse(result)
        dest = cast(MemNode, update.destination)
        self.assertEqual(dest.value.evaluate(), 0)
        self.assertIsInstance(update.source, Number)

    def testUpdateReplace(self):
        program = self.createProgram("1 = 1 --> mem[0] := 1 mem[1] := 2;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        update1 = cast(Update, rule.commands[0])
        update2 = cast(Update, rule.commands[1])

        result = mutator.mutateUpdateReplace((update1, rule))

        self.assertTrue(result)
        # update1 should have been replaced with a copy of update2
        replaced_command = rule.commands[0]
        self.assertIsNot(replaced_command, update1)
        self.assertIsNot(replaced_command, update2)  # Needs to be a copy!
        self.assertEqual(str(replaced_command), str(update2))

    def testUpdateReplaceFailsIfOnlyOneUpdate(self):
        program = self.createProgram("1 = 1 --> mem[0] := 1;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        update = cast(Update, rule.commands[0])

        result = mutator.mutateUpdateReplace((update, rule))

        self.assertFalse(result)
        self.assertIs(rule.commands[0], update)

    def testActionTransformToServe(self):
        program = self.createProgram("1 = 1 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        action = cast(Action, rule.commands[0])

        # Transform to a serve action
        mutator.mutateActionTransform((action, rule), TOKENS.T_SERVE)
        self.assertIsInstance(rule.commands[0], ServeAction)
        serve = cast(ServeAction, rule.commands[0])
        self.assertIsInstance(serve.value, ExpressionNode)
        self.assertEqual(serve.actionType.lexeme, "serve")

    def testActionTransformFromServe(self):
        program = self.createProgram("1 = 1 --> serve[10];")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule = program.rules[0]
        action = cast(Action, rule.commands[0])

        # Transform away from a serve action
        mutator.mutateActionTransform((action, rule), TOKENS.T_FORWARD)
        self.assertIsInstance(rule.commands[0], Action)
        self.assertNotIsInstance(rule.commands[0], ServeAction)
        newAction = cast(Action, rule.commands[0])
        self.assertEqual(newAction.actionType.lexeme, "forward")

    def testProgramSwap(self):
        program = self.createProgram("1 = 1 --> wait; 2 = 2 --> forward;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        rule1 = program.rules[0]
        rule2 = program.rules[1]

        result = mutator.mutateSwapProgram((program, ast))

        self.assertTrue(result)
        self.assertIs(program.rules[0], rule2)
        self.assertIs(program.rules[1], rule1)

    def testProgramSwapFailsIfOnlyOneRule(self):
        program = self.createProgram("1 = 1 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        result = mutator.mutateSwapProgram((program, ast))
        self.assertFalse(result)

    def testProgramDuplicate(self):
        program = self.createProgram("1 = 1 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        initialNodeCount = ast.nodeCount
        self.assertEqual(len(program.rules), 1)

        result = mutator.mutateDuplicateProgram((program, ast))

        self.assertTrue(result)
        self.assertEqual(len(program.rules), 2)
        self.assertEqual(str(program.rules[0]), str(program.rules[1]))
        self.assertGreater(ast.nodeCount, initialNodeCount)

    def testProgramDuplicateWithTarget(self):
        program = self.createProgram("1 = 1 --> wait; 2 = 2 --> forward;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        target_rule = program.rules[1]
        result = mutator.mutateDuplicateProgram((program, ast), target=target_rule)

        self.assertTrue(result)
        self.assertEqual(len(program.rules), 3)
        # Count rules containing "forward" since it can be inserted anywhere
        forward_rules = [r for r in program.rules if "forward" in str(r)]
        self.assertEqual(len(forward_rules), 2)
