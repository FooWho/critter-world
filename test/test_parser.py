import unittest
from lexer import Lexer
from parser import Parser
from schemas import TOKENS, CritterParseError
from typing import cast, LiteralString
from abstractSyntaxTree import (
    MemNode, SensorNode, Number, RelationalOperator, Expression, Term, Factor
)

class TestParser(unittest.TestCase):

    def get_parser(self, code: str) -> Parser:
        lexer = Lexer()
        tokens = lexer.tokenize(code)
        return Parser(tokens)

    def testParseNumber(self):
        testStr = '0 42 54 33 101 102872354 456 567'
        numStrs:list[LiteralString] = testStr.split()
        parser = self.get_parser(testStr)
        for i in range(len(numStrs)):
            node = parser.parseNumber()
            node = cast(Number, node)
            self.assertIsInstance(node, Number)
            self.assertEqual(node.number.tokenType, TOKENS.T_NUMBER)
            self.assertEqual(node.number.lexeme, numStrs[i])
            self.assertEqual(node.value, int(numStrs[i]))

    def testParseMemNode(self):
        testStr = 'mem[10] mem[0] mem[3]'
        memStrs:list[LiteralString] = testStr.split()
        parser = self.get_parser(testStr)
        for i in range(len(memStrs)):
            node = parser.parseMemNode()
            self.assertIsInstance(node, MemNode)
            self.assertIsInstance(node.expression, Expression)
            self.assertIsInstance(node.expression.expression, Term)
            termNode = cast(Term, node.expression.expression)
            self.assertIsInstance(termNode.term, Factor)
            factorNode = cast(Factor, termNode.term)
            self.assertIsInstance(factorNode.factor, Number)
            numberNode = cast(Number, factorNode.factor) 
            tst = self.helperForMemNode(memStrs[i])
            self.assertEqual(numberNode.number.lexeme, tst[0])
            self.assertEqual(numberNode.value, tst[1])

    def helperForMemNode(self, token: str) -> tuple[str, int]:
        num = token.strip('mem[').rstrip(']')
        return (num, int(num))

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
