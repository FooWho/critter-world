import unittest
from lexer import Lexer
from parser import Parser
from schemas import TOKENS, CritterParseError, TokenLexeme, Token
from typing import cast, LiteralString
from abstractSyntaxTree import (
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
    countNodes,
)


class TestAST(unittest.TestCase):

    def testNumber(self):
        number = Number(Token(TOKENS.T_NUMBER, "5", 0, 0))
        self.assertEqual(number.getValue(), 5)
        self.assertEqual(number.evaluate(), 5)
        number.setValue(6)
        self.assertEqual(number.getValue(), 6)
        self.assertEqual(countNodes(number), 1)

    def testMemNode(self):
        number10 = Number(Token(TOKENS.T_NUMBER, "10", 0, 0))
        memNode1 = MemNode(number10)
        self.assertEqual(memNode1.getValue(), number10)
        self.assertEqual(countNodes(memNode1), 2)
        number5 = Number(Token(TOKENS.T_NUMBER, "5", 0, 0))
        number15 = Number(Token(TOKENS.T_NUMBER, "15", 0, 0))
        memNode2 = MemNode(number5)
        self.assertEqual(str(memNode2), "PASS")
        self.assertEqual(MemNode.desugar(Token(TOKENS.T_PASS, "PASS", 0, 0)), memNode2)
        binOp = BinaryOperator(number5, TokenLexeme(TOKENS.T_PLUS, "+"), number10)
        memNode3 = MemNode(number15)
        memNode4 = MemNode(binOp)
        self.assertEqual(memNode3, memNode4)
