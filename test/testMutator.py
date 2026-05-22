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
        program = self.createProgram("1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)

        parentNode = cast(RelationalOperator, program.rules[0].condition)
        originalNode: Number = cast(Number, parentNode.leftOperand)
        mutator.mutateTransformNumber((originalNode, parentNode), -5)
        mutation = parentNode.leftOperand
        self.assertIsInstance(mutation, UnaryOperator)
        self.assertEqual(mutation.evaluate(), -4)
        originalNode = cast(Number, parentNode.rightOperand)
        self.assertEqual(originalNode.evaluate(), 3)
        mutator.mutateTransformNumber((originalNode, parentNode), 4)
        self.assertIsInstance(parentNode.rightOperand, Number)
        mutation = cast(Number, parentNode.rightOperand)
        self.assertEqual(mutation.evaluate(), 7)

        program = self.createProgram("-1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
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

    def testMutateInsertNumber(self):
        program = self.createProgram("1 < 2 --> wait;")
        ast = AbstractSyntaxTree(program)

        mutator = Mutator(ast)
        condition = cast(RelationalOperator, program.rules[0].condition)
        faultLocus = (
            cast(Number, condition.leftOperand),
            condition,
        )
        mutator.mutateInsertNumber(faultLocus, 1)
        self.assertIsInstance(condition.leftOperand, UnaryOperator)

        faultLocus = (
            cast(Number, cast(UnaryOperator, condition.leftOperand).operand),
            condition.leftOperand,
        )
        mutator.mutateInsertNumber(faultLocus, 1)
        self.assertIsInstance(condition.leftOperand, Number)

        faultLocus = (cast(Number, condition.rightOperand), condition)
        mutator.mutateInsertNumber(faultLocus, 2)
        self.assertIsInstance(condition.rightOperand, BinaryOperator)
        print(f"{ast.rootNode.rules[0].condition}")

    def testMutateReplaceNumber(self):

        program = self.createProgram("1 + 4 < 2 * 17 mod 12 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator = Mutator(ast)
        replacementNode = program.rules[0].condition.rightOperand.leftOperand
        originalNode = program.rules[0].condition.leftOperand.rightOperand
        parentNode = program.rules[0].condition.leftOperand
        print(f"({originalNode},{parentNode})")
        mutator.mutateReplaceNumber(
            (cast(Number, originalNode), parentNode), cast(Number, replacementNode)
        )
        self.assertEqual("1 + 2 * 17 < 2 * 17 mod 12", str(program.rules[0].condition))
