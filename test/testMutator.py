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
from mutator import Mutator


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
            self.assertTrue(childNode in parentNode)

    def testMutateTransformNumberNegativeToZero(self):
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
        mutator.mutateTransformNumber((originalNode, parentNode), -1)
        self.assertIsInstance(condition.leftOperand, UnaryOperator)
        mutation = cast(UnaryOperator, condition.leftOperand)
        self.assertEqual(mutation.evaluate(), 0)
        self.assertEqual(ast.nodeCount, 7)
        self.assertEqual(str(condition), "-0 < 3")

    def testMutateTransformNumberPositiveToNegative(self):
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
        mutator.mutateTransformNumber((originalNode, parentNode), -4)
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

    def testMutateTransformNumberPositiveToPositive(self):
        # Positive to Positive
        program = self.createProgram("1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        self.assertEqual(ast.nodeCount, 6)
        condition = cast(RelationalOperator, program.rules[0].condition)
        parentNode = cast(RelationalOperator, condition)
        originalNode = cast(Number, parentNode.leftOperand)
        mutator.mutateTransformNumber((originalNode, parentNode), 4)  # 1 + 4 = 5
        self.assertIsInstance(condition.leftOperand, Number)
        self.assertEqual(condition.leftOperand.evaluate(), 5)
        self.assertEqual(ast.nodeCount, 6)

    def testMutateTransformNumberNegativeToDoubleNegative(self):
        # Negative to Double Negative
        program = self.createProgram("-2 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        self.assertEqual(ast.nodeCount, 7)
        condition = cast(RelationalOperator, program.rules[0].condition)
        parentNode = cast(UnaryOperator, condition.leftOperand)
        originalNode = cast(Number, parentNode.operand)
        mutator.mutateTransformNumber(
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

    def testMutateInsertNumberUnaryOperator(self):
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
        mutator.mutateInsertNumber(faultLocus, 1)
        # Left operand of the condition is now a UnaryOperand instead of a Number
        self.assertIsInstance(condition.leftOperand, UnaryOperator)
        self.assertEqual(str(condition), "-1 < 2")

    def testMutateInsertNumberUnaryOperatorDoubleNegative(self):
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
        mutator.mutateInsertNumber(faultLocus, 1)
        self.assertIsInstance(condition.leftOperand, UnaryOperator)
        self.assertEqual(str(condition), "--1 < 2")
        self.assertEqual(ast.nodeCount, 8)

    def testMutateInsertNumberBinaryOperator(self):
        # Set a new faultLocus. Insert a BinaryOperator as as the parent of the "2" in "1 < 2"
        program = self.createProgram("1 < 2 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        self.assertEqual(ast.nodeCount, 6)
        condition = cast(RelationalOperator, program.rules[0].condition)
        faultLocus = (cast(Number, condition.rightOperand), condition)
        mutator.mutateInsertNumber(faultLocus, 2)
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

    def testMutateInsertNumberMemNodeOrDirectedSensorNode(self):
        program = self.createProgram("1 < 2 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        # Set a new faultLocus. Insert a MemNode or DirectedSensorNode (Choice 3)
        condition = cast(RelationalOperator, program.rules[0].condition)
        faultLocus = (cast(Number, condition.leftOperand), condition)
        mutator.mutateInsertNumber(faultLocus, 3)
        self.assertTrue(
            isinstance(condition.leftOperand, MemNode)
            or isinstance(condition.leftOperand, DirectedSensorNode)
        )
        newNode = cast(MemNode | DirectedSensorNode, condition.leftOperand)
        self.assertIsInstance(newNode.value, Number)
        self.assertTrue(newNode.value.evaluate() == 1)

    def testMutateReplaceNumber(self):
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

        mutator.mutateReplaceNumber(
            (cast(Number, originalNode), binaryOperationNode),
            cast(ExpressionNode, replacementNode),
        )
        self.assertEqual("1 + 2 * 17 < 2 * 17 mod 12", str(program.rules[0].condition))

    def testMutateReplaceMemNodeDestination(self):
        program = self.createProgram("1 = 1 --> mem[0] := 5;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        update = cast(Update, program.rules[0].commands[0])
        originalNode = cast(MemNode, update.destination)

        # We need a new MemNode to replace it with
        replacement = MemNode(Number(value=2))

        mutator.mutateReplaceMemNode((originalNode, update), replacement)

        self.assertIsInstance(update.destination, MemNode)
        update.destination = cast(MemNode, update.destination)
        self.assertEqual(update.destination.value.evaluate(), 2)

    def testMutateReplaceMemNodeFailsIfOnlyOneMemNode(self):
        # Program with exactly one MemNode
        program = self.createProgram("1 = 1 --> mem[0] := 5;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        update = cast(Update, program.rules[0].commands[0])
        originalNode = cast(MemNode, update.destination)

        # Do not pass a replacement node. It should return False because it cannot find another MemNode to swap with.
        result = mutator.mutateReplaceMemNode((originalNode, update))
        self.assertFalse(result)

    def testMutateReplaceMemNodeSource(self):
        program = self.createProgram("1 = 1 --> MEMSIZE := mem[3];")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        update = cast(Update, program.rules[0].commands[0])
        originalNode = cast(MemNode, update.source)

        # Replace it with a Number
        replacement = Number(value=42)
        mutator.mutateReplaceMemNode((originalNode, update), replacement)

        self.assertIsInstance(update.source, Number)
        update.source = cast(Number, update.source)
        self.assertEqual(update.source.evaluate(), 42)

    def testMutateInsertMemNodeUnary(self):
        program = self.createProgram("1 = mem[0] --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        originalNode = cast(MemNode, condition.rightOperand)

        mutator.mutateInsertMemNode((originalNode, condition), 0)
        self.assertIsInstance(condition.rightOperand, UnaryOperator)
        unary = cast(UnaryOperator, condition.rightOperand)
        self.assertIsInstance(unary.operand, MemNode)

    def testMutateInsertMemNodeBinary(self):
        program = self.createProgram("1 = mem[0] --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        originalNode = cast(MemNode, condition.rightOperand)

        mutator.mutateInsertMemNode((originalNode, condition), 1)
        self.assertIsInstance(condition.rightOperand, BinaryOperator)

    def testMutateInsertMemNodeSensor(self):
        program = self.createProgram("1 = mem[0] --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        originalNode = cast(MemNode, condition.rightOperand)

        mutator.mutateInsertMemNode((originalNode, condition), 2)
        self.assertIsInstance(condition.rightOperand, DirectedSensorNode)

    def testMutateInsertMemNodeAsMemNode(self):
        program = self.createProgram("1 = mem[0] --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        originalNode = cast(MemNode, condition.rightOperand)

        # Insert a MemNode wrapper (Choice 3)
        mutator.mutateInsertMemNode((originalNode, condition), 3)
        self.assertIsInstance(condition.rightOperand, MemNode)
        outerMem = cast(MemNode, condition.rightOperand)
        self.assertIsInstance(outerMem.value, MemNode)

    def testMutateInsertMemNodeDestination(self):
        # Start with mem[0] := 5
        program = self.createProgram("1 = 1 --> mem[0] := 5;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        update = cast(Update, program.rules[0].commands[0])
        originalNode = cast(MemNode, update.destination)

        # Do an insertion. Because it's a destination, it MUST force choice 3 and wrap it in a MemNode
        mutator.mutateInsertMemNode((originalNode, update))

        self.assertIsInstance(update.destination, MemNode)
        outerMem = cast(MemNode, update.destination)
        self.assertIsInstance(outerMem.value, MemNode)

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

    def testUnaryReplaceChildDoubleNegative(self):
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
