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

    def testMutateTransformNumber(self):
        mutator = Mutator()
        program = self.createProgram("----5 = 5 --> wait;")
        ast = AbstractSyntaxTree(program)
        q = ast.rootNode.rules[0].condition.leftOperand.evaluate()
        print(f"{q}")
        program = self.createProgram("1 < 3 --> wait;")
        ast = AbstractSyntaxTree(program)
        mutator.ast = ast
        parentNode = cast(RelationalOperator, program.rules[0].condition)
        originalNode: Number = cast(Number, parentNode.leftOperand)
        mutator.mutateTransformNumber((originalNode, parentNode), -5)
        mutation = parentNode.leftOperand
        self.assertIsInstance(mutation, UnaryOperator)
        self.assertTrue(mutation is parentNode.leftOperand)
        self.assertFalse(originalNode is parentNode.leftOperand)
        self.assertEqual(mutation.evaluate(), -4)
        originalNode = cast(Number, parentNode.rightOperand)
        self.assertEqual(originalNode.evaluate(), 3)
        mutator.mutateTransformNumber((originalNode, parentNode), 4)
        self.assertTrue(originalNode is parentNode.rightOperand)
        self.assertEqual(originalNode.evaluate(), 7)

    def createProgram(self, programString: str) -> Program:
        parser = Parser(Lexer().tokenize(programString))
        program = parser.parse()
        return program
