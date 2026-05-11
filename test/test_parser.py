import unittest
from lexer import Lexer
from parser import Parser
from schemas import TOKENS, CritterParseError
from typing import cast, LiteralString
from abstractSyntaxTree import (
    MemNode, SensorNode, Number, RelationalOperator, LogicalOperator, BinaryOperator, UnaryOperator
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
        testStr = 'mem[10] mem[5] mem[3] mem[17]'
        memStrs:list[LiteralString] = testStr.split()
        parser = self.get_parser(testStr)
        for i in range(len(memStrs)):
            node = parser.parseMemNode()
            self.assertIsInstance(node, MemNode)
            node = node.getValue()
            self.assertIsInstance(node, Number)
            node = cast(Number, node)
            tst = self.helperForMemNode(memStrs[i])
            self.assertEqual(node.number.lexeme, tst[0])
            self.assertEqual(node.value, tst[1])

    def helperForMemNode(self, token: str) -> tuple[str, int]:
        num = token.strip('mem[').rstrip(']')
        return (num, int(num))

    def testParseSensor(self):
        testStr = 'ahead[2] nearby[3] random[4] smell'
        sensorStrs: list[LiteralString] = testStr.split()
        parser = self.get_parser(testStr)
        for i in range(len(sensorStrs)):
            node = parser.parseSensor()          
            self.assertIsInstance(node, SensorNode)
            tst = self.helperForSensorNode(sensorStrs[i])
            self.assertEqual(node.getSensorType().tokenType, tst[0])
            if node.getSensorType().tokenType is not TOKENS.T_SMELL:
                self.assertEqual(node.getValue().evaluate(), tst[2])

    def helperForSensorNode(self, token: str) -> tuple[TOKENS, str, int]:
        if not token.find('ahead'):
            num = token.strip('ahead[').rstrip(']')
            return (TOKENS.T_AHEAD, num, int(num))
        elif not token.find('nearby'):
            num = token.strip('nearby[').rstrip(']')
            return (TOKENS.T_NEARBY, num, int(num))
        elif not token.find('random'):
            num = token.strip('random[').rstrip(']')
            return (TOKENS.T_RANDOM, num, int(num))
        elif not token.find('smell'):
            return (TOKENS.T_SMELL, '-1', -1)
        else:
            raise ValueError('Token does not have a <Sensor> with <Number> or "smell".')

    def testParseRelation(self):
        parser = self.get_parser('mem[0] >= 5')
        node = parser.parseRelation()
        self.assertIsInstance(node, RelationalOperator)
        node = cast(RelationalOperator, node)
        self.assertEqual(node.operator.lexeme, '>=')

    def testParseExpressionWithAddOps(self):
        parser = self.get_parser("5 + 3 - 2")
        node = parser.parseExpression()
        self.assertIsNotNone(node)

    def testCritterParseErrorInvalidSyntax(self):
        parser = self.get_parser('mem 5') 
        with self.assertRaises(CritterParseError):
            parser.parseMemNode()

    def testParseFactorSugar(self):
        parser = self.get_parser('MEMSIZE DEFENSE OFFENSE')
        
        node = parser.parseFactor()
        self.assertIsInstance(node, MemNode)
        node = cast(MemNode, node)
        self.assertEqual(node.getValue().evaluate(), 0)
        
        node = parser.parseFactor()
        self.assertIsInstance(node, MemNode)
        node = cast(MemNode, node)
        self.assertEqual(node.getValue().evaluate(), 1)
        
        node = parser.parseFactor()
        self.assertIsInstance(node, MemNode)
        node = cast(MemNode, node)
        self.assertEqual(node.getValue().evaluate(), 2)

    def testParseUnaryOperator(self):
        parser = self.get_parser('-5 -mem[1]')
        node = parser.parseFactor()
        self.assertIsInstance(node, UnaryOperator)
        self.assertEqual(node.evaluate(), -5)

        node = parser.parseFactor()
        self.assertIsInstance(node, UnaryOperator)
        node = cast(UnaryOperator, node)
        self.assertIsInstance(node.operand, MemNode)

    def testParseExpressionPrecedence(self):
        parser = self.get_parser('2 * 3 + 4')
        node = parser.parseExpression()
        self.assertIsInstance(node, BinaryOperator)
        node = cast(BinaryOperator, node)
        self.assertEqual(node.operator.lexeme, '+')
        self.assertEqual(node.evaluate(), 10)
        parser = self.get_parser('2 * (3 + 4)')
        node = parser.parseExpression()
        self.assertEqual(node.evaluate(), 14)
        parser = self.get_parser('((2 + 4) * 3) * (3 + 4)')
        node = parser.parseExpression()
        self.assertEqual(node.evaluate(), 126)

    def testUnbalancedParens(self):
        with self.assertRaises(CritterParseError):
            parser = self.get_parser('((2 * 3) + 4')
            parser.parseExpression()
            parser = self.get_parser('(2 * 3)) + 4')
            parser.parseExpression()

    def testParseConditionTrue(self):
        parser = self.get_parser('1 = 1 and 2 = 2 or 3 = 3')
        node = parser.parseCondition()
        self.assertIsInstance(node, LogicalOperator)
        node = cast(LogicalOperator, node)
        self.assertEqual(node.operator.tokenType, TOKENS.T_OR)
        nodeLeft = node.leftOperand
        nodeRight = node.rightOperand
        self.assertIsInstance(nodeLeft, LogicalOperator)
        self.assertEqual(nodeLeft.operator.tokenType, TOKENS.T_AND)
        self.assertIsInstance(nodeRight, RelationalOperator)
        self.assertEqual(nodeRight.operator.tokenType, TOKENS.T_EQU)
        self.assertEqual(node.evaluate(), True)

    def testParseConditionFalse(self):
        parser = self.get_parser('1 < 1 and 2 = 2 or 3 != 3')
        node = parser.parseCondition()
        self.assertIsInstance(node, LogicalOperator)
        node = cast(LogicalOperator, node)
        self.assertEqual(node.operator.tokenType, TOKENS.T_OR)
        nodeLeft = node.leftOperand
        nodeRight = node.rightOperand
        self.assertIsInstance(nodeLeft, LogicalOperator)
        self.assertEqual(nodeLeft.operator.tokenType, TOKENS.T_AND)
        self.assertIsInstance(nodeRight, RelationalOperator)
        self.assertEqual(nodeRight.operator.tokenType, TOKENS.T_NEQU)
        self.assertEqual(node.evaluate(), False)

    def testLogicalPrecedence(self):
        parser = self.get_parser('1 = 1 or 2 = 2 and 5 = 3')
        node = parser.parseCondition()
        self.assertEqual(node.evaluate(), True)
        parser = self.get_parser('{1 = 1 or 2 = 2} and 5 = 3')
        node = parser.parseCondition()
        self.assertEqual(node.evaluate(), False)
