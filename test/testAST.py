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
    countNodes,
)


class TestAST(unittest.TestCase):

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

    def testNumber(self):
        number = Number(Token(TOKENS.T_NUMBER, "5", 0, 0))
        self.assertEqual(number.value, 5)
        self.assertEqual(number.evaluate(), 5)
        number.value = 6
        self.assertEqual(number.value, 6)
        self.assertEqual(countNodes(number), 1)

    def testMemNode(self):
        number10 = Number(Token(TOKENS.T_NUMBER, "10", 0, 0))
        memNode1 = MemNode(number10)
        self.assertEqual(memNode1.value, number10)
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

    def testBinaryOperator(self):
        num5 = Number(Token(TOKENS.T_NUMBER, "5", 0, 0))
        num3 = Number(Token(TOKENS.T_NUMBER, "3", 0, 0))
        binOp = BinaryOperator(num5, TokenLexeme(TOKENS.T_PLUS, "+"), num3)
        self.assertEqual(binOp.evaluate(), 8)
        self.assertEqual(str(binOp), "5 + 3")

        num2 = Number(Token(TOKENS.T_NUMBER, "2", 0, 0))
        mulOp = BinaryOperator(binOp, TokenLexeme(TOKENS.T_STAR, "*"), num2)
        self.assertEqual(mulOp.evaluate(), 16)
        # Asserts that breaking precedence wraps the inner operation in parentheses
        self.assertEqual(str(mulOp), "(5 + 3) * 2")

    def testUnaryOperator(self):
        num = Number(Token(TOKENS.T_NUMBER, "10", 0, 0))
        unOp = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, "-"), num)
        self.assertEqual(unOp.evaluate(), -10)
        self.assertEqual(str(unOp), "-10")

    def testRelationalOperator(self):
        num5 = Number(Token(TOKENS.T_NUMBER, "5", 0, 0))
        num3 = Number(Token(TOKENS.T_NUMBER, "3", 0, 0))
        relOp = RelationalOperator(num5, TokenLexeme(TOKENS.T_GREAT, ">"), num3)
        self.assertTrue(relOp.evaluate())
        self.assertEqual(str(relOp), "5 > 3")

    def testLogicalOperator(self):
        num5 = Number(Token(TOKENS.T_NUMBER, "5", 0, 0))
        num3 = Number(Token(TOKENS.T_NUMBER, "3", 0, 0))
        trueRel = RelationalOperator(num5, TokenLexeme(TOKENS.T_GREAT, ">"), num3)
        falseRel = RelationalOperator(num5, TokenLexeme(TOKENS.T_LESS, "<"), num3)

        logOp = LogicalOperator(trueRel, TokenLexeme(TOKENS.T_AND, "and"), falseRel)
        self.assertFalse(logOp.evaluate())
        self.assertEqual(str(logOp), "5 > 3 and 5 < 3")

    def testCommands(self):
        mem = MemNode(Number(Token(TOKENS.T_NUMBER, "0", 0, 0)))
        num = Number(Token(TOKENS.T_NUMBER, "10", 0, 0))
        update = Update(mem, num)
        self.assertEqual(str(update), "MEMSIZE := 10")

        serve = ServeAction(Token(TOKENS.T_SERVE, "serve", 0, 0), num)
        self.assertEqual(str(serve), "serve[10]")

    def testNodeCount(self):
        self.assertEqual(self.astCritter1.nodeCount, 150)
        self.assertEqual(self.astCritter2.nodeCount, 150)
        self.assertEqual(self.astCritter3.nodeCount, 9)

    def testGetExpressions(self):
        expressions = self.astCritter1.getNodesByType(ExpressionNode)
        self.assertEqual(len(expressions), 89)

        expressions = self.astCritter2.getNodesByType(ExpressionNode)
        self.assertEqual(len(expressions), 89)

        expressions = self.astCritter3.getNodesByType(ExpressionNode)
        self.assertEqual(len(expressions), 6)
