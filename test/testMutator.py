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

    def testMutateTransformNumber(self):
        # Negative to Positive
        # UnaryNode should go away -- left operand goes from UnaryOperand(1) to 4. UnaryOperator(1) + 5 = 4.
        # Node count chages from 6 to 5 because UnaryNode is gone.
        program = self.createProgram("-1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        # 6 Nodes to begin: Rule, RelationalOperator, UnaryOperator, Number, Number, Action
        self.assertEqual(ast.nodeCount, 6)
        # Program(Rules[0](RelationalOperator(UnaryOperator(1),3)-->wait))
        # UnaryOperator(1)
        parentNode = cast(
            UnaryOperator,
            cast(RelationalOperator, program.rules[0].condition).leftOperand,
        )
        # 1
        originalNode: Number = cast(Number, parentNode.operand)

        # After mutation -> Program(Rules[0](RelationalOperator(4,3)-->wait))
        mutator.mutateTransformNumber((originalNode, parentNode), 5)

        # RelationalOperator(4,3)
        parentNode = cast(
            RelationalOperator, cast(RelationalOperator, program.rules[0].condition)
        )
        # 4
        mutation = parentNode.leftOperand
        self.assertIsInstance(mutation, Number)
        self.assertEqual(mutation.evaluate(), 4)

        # Now only 5 nodes: Rule, RelatinalOperator, Number, Number, Action
        self.assertEqual(ast.nodeCount, 5)

        # Negative to Zero
        # UnaryNode should go away -- left operand goes from UnaryOperand(1) to 0. UnaryOperand(1) + 1 = 0
        program = self.createProgram("-1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        self.assertEqual(ast.nodeCount, 6)
        condition = cast(RelationalOperator, program.rules[0].condition)
        parentNode = condition.leftOperand
        self.assertIsInstance(parentNode, UnaryOperator)
        self.assertEqual(parentNode.evaluate(), -1)
        parentNode = cast(UnaryOperator, parentNode)
        originalNode = cast(Number, parentNode.operand)
        self.assertEqual(originalNode.value, 1)
        mutator.mutateTransformNumber((originalNode, parentNode), 1)
        self.assertIsInstance(condition.leftOperand, Number)
        mutation = cast(Number, condition.leftOperand)
        self.assertEqual(mutation.value, 0)
        self.assertEqual(ast.nodeCount, 5)

        # Positive to Negative
        # UnaryNode should get added -- left operand goes from 1 to UnaryOperator(3). 1 + (-4) = UnaryOperator(3)
        # Node cound goes from 5 to 6.
        program = self.createProgram("1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        self.assertEqual(ast.nodeCount, 5)
        self.assertIsInstance(program.rules[0].condition, RelationalOperator)
        parentNode = cast(RelationalOperator, program.rules[0].condition)
        self.assertIsInstance(parentNode.leftOperand, Number)
        originalNode = cast(Number, parentNode.leftOperand)
        self.assertEqual(originalNode.value, originalNode.evaluate())
        self.assertEqual(originalNode.evaluate(), 1)
        mutator.mutateTransformNumber((originalNode, parentNode), -4)
        self.assertEqual(ast.nodeCount, 6)
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
        self.assertEqual(ast.nodeCount, 6)

    def testMutateInsertNumber(self):
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

        # Set new faultLocus. We are now going to insert a UnaryOperator as the parent
        # of the -1 in the expression "-1 < 2". This would create a double negative.
        # The resulting expression will actually be "1 < 2"
        faultLocus = (
            cast(Number, cast(UnaryOperator, condition.leftOperand).operand),
            condition.leftOperand,
        )
        mutator.mutateInsertNumber(faultLocus, 1)
        self.assertIsInstance(condition.leftOperand, Number)
        self.assertEqual(str(condition), "1 < 2")

        # Set a new faultLocus. Insert a BinaryOperator as as the parent of the "2" in "1 < 2"
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

        print(f"({originalNode},{binaryOperationNode})")
        mutator.mutateReplaceNumber(
            (cast(Number, originalNode), binaryOperationNode),
            cast(ExpressionNode, replacementNode),
        )
        self.assertEqual("1 + 2 * 17 < 2 * 17 mod 12", str(program.rules[0].condition))

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
        # Test double negative collapsing logic in UnaryOperator
        program = self.createProgram("-1 = -1 --> wait;")
        ast = AbstractSyntaxTree(program)
        condition = cast(RelationalOperator, program.rules[0].condition)
        unaryOp = cast(UnaryOperator, condition.leftOperand)

        newChild = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), Number(value=5))
        unaryOp.replaceChild(unaryOp.operand, newChild)

        # The double negative should collapse and set the grandparent's child to the operand
        self.assertIsInstance(condition.leftOperand, Number)
        self.assertEqual(condition.leftOperand.evaluate(), 5)
