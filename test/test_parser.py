import unittest
from lexer import Lexer
from parser import Parser
from schemas import TOKENS, CritterParseError
from typing import cast
from abstractSyntaxTree import (
    MemNode, SensorNode, Number, RelationalOperator, Expression, Term, Factor
)

class TestParser(unittest.TestCase):

    def get_parser(self, code: str) -> Parser:
        lexer = Lexer()
        tokens = lexer.tokenize(code)
        return Parser(tokens)

    def testParseNumber(self):
        parser = self.get_parser("42")
        node = parser.parseNumber()
        self.assertIsInstance(node, Number)
        self.assertEqual(node.number.lexeme, '42')

    def testParseMemNode(self):
        parser = self.get_parser("mem[10]")
        node = parser.parseMemNode()
        self.assertIsInstance(node, MemNode)
        self.assertIsInstance(node.expression, Expression)
        self.assertIsInstance(node.expression.expression, Term)
        termNode = cast(Term, node.expression.expression)
        self.assertIsInstance(termNode.term, Factor)
        factorNode = cast(Factor, termNode.term)
        self.assertIsInstance(factorNode.factor, Number)
        numberNode = cast(Number, factorNode.factor) 
        self.assertEqual(numberNode.number.lexeme, '10')
        self.assertEqual(numberNode.value, 10)
        
    def testParseSensor(self):
        parser = self.get_parser("ahead[2]")
        node = parser.parseSensor()
        self.assertIsInstance(node, SensorNode)
        self.assertEqual(node.sensorType, TOKENS.T_AHEAD)
        
    def testParseRelationalOperator(self):
        parser = self.get_parser("mem[0] >= 5")
        node = parser.parseRelationalOperator()
        self.assertIsInstance(node, RelationalOperator)
        self.assertEqual(node.operator.lexeme, ">=")

    def testParseExpressionWithAddOps(self):
        parser = self.get_parser("5 + 3 - 2")
        node = parser.parseExpression()
        self.assertIsNotNone(node)

    def testCritterParseErrorInvalidSyntax(self):
        parser = self.get_parser("mem 5") 
        with self.assertRaises(CritterParseError):
            parser.parseMemNode()
