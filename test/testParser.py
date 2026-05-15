import unittest
from lexer import Lexer
from parser import Parser
from schemas import TOKENS, CritterParseError, TokenLexeme
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
)


class TestParser(unittest.TestCase):

    def getParser(self, code: str) -> Parser:
        lexer = Lexer()
        tokens = lexer.tokenize(code)
        return Parser(tokens)

    def testParseNumber(self):
        testStr = "0 42 54 33 101 102872354 456 567"
        numStrs: list[LiteralString] = testStr.split()
        parser = self.getParser(testStr)
        for i in range(len(numStrs)):
            node = parser.parseNumber()
            node = cast(Number, node)
            self.assertIsInstance(node, Number)
            self.assertEqual(node.number.tokenType, TOKENS.T_NUMBER)
            self.assertEqual(node.number.lexeme, numStrs[i])
            self.assertEqual(node.value, int(numStrs[i]))

    def testParseMemNode(self):
        testStr = "mem[10] mem[5] mem[3] mem[17]"
        memStrs: list[LiteralString] = testStr.split()
        parser = self.getParser(testStr)
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
        num = token.strip("mem[").rstrip("]")
        return (num, int(num))

    def testParseSensor(self):
        testStr = "ahead[2] nearby[3] random[4] smell"
        sensorStrs: list[LiteralString] = testStr.split()
        parser = self.getParser(testStr)
        for i in range(len(sensorStrs)):
            node = parser.parseSensor()
            self.assertIsInstance(node, SensorNode)
            tst = self.helperForSensorNode(sensorStrs[i])
            self.assertEqual(node.getSensorType().tokenType, tst[0])
            if isinstance(node, DirectedSensorNode):
                self.assertEqual(node.getValue().evaluate(), tst[2])
            elif isinstance(node, SmellNode):
                self.assertEqual(tst[0], TOKENS.T_SMELL)

    def helperForSensorNode(self, token: str) -> tuple[TOKENS, str, int]:
        if not token.find("ahead"):
            num = token.strip("ahead[").rstrip("]")
            return (TOKENS.T_AHEAD, num, int(num))
        elif not token.find("nearby"):
            num = token.strip("nearby[").rstrip("]")
            return (TOKENS.T_NEARBY, num, int(num))
        elif not token.find("random"):
            num = token.strip("random[").rstrip("]")
            return (TOKENS.T_RANDOM, num, int(num))
        elif not token.find("smell"):
            return (TOKENS.T_SMELL, "-1", -1)
        else:
            raise ValueError('Token does not have a <Sensor> with <Number> or "smell".')

    def testParseRelation(self):
        parser = self.getParser("mem[0] >= 5")
        node = parser.parseRelation()
        self.assertIsInstance(node, RelationalOperator)
        node = cast(RelationalOperator, node)
        self.assertEqual(node.operator.lexeme, ">=")

    def testParseExpressionWithAddOps(self):
        parser = self.getParser("5 + 3 - 2")
        node = parser.parseExpression()
        self.assertIsNotNone(node)

    def testCritterParseErrorInvalidSyntax(self):
        parser = self.getParser("mem 5")
        with self.assertRaises(CritterParseError):
            parser.parseMemNode()

    def testParseFactorSugar(self):
        parser = self.getParser("MEMSIZE DEFENSE OFFENSE")

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
        parser = self.getParser("-5 -mem[1]")
        node = parser.parseFactor()
        self.assertIsInstance(node, UnaryOperator)
        self.assertEqual(node.evaluate(), -5)

        node = parser.parseFactor()
        self.assertIsInstance(node, UnaryOperator)
        node = cast(UnaryOperator, node)
        self.assertIsInstance(node.operand, MemNode)

    def testParseExpressionPrecedence(self):
        parser = self.getParser("2 * 3 + 4")
        node = parser.parseExpression()
        self.assertIsInstance(node, BinaryOperator)
        node = cast(BinaryOperator, node)
        self.assertEqual(node.operator.lexeme, "+")
        self.assertEqual(node.evaluate(), 10)
        parser = self.getParser("2 * (3 + 4)")
        node = parser.parseExpression()
        self.assertEqual(node.evaluate(), 14)
        parser = self.getParser("((2 + 4) * 3) * (3 + 4)")
        node = parser.parseExpression()
        self.assertEqual(node.evaluate(), 126)

    def testUnbalancedParens(self):
        parser = self.getParser("((2 * 3) + 4")
        with self.assertRaises(CritterParseError):
            parser.parseExpression()

        parser = self.getParser("(2 * 3)) + 4 > 5")
        with self.assertRaises(CritterParseError):
            parser.parseRelation()

    def testParseConditionTrue(self):
        parser = self.getParser("1 = 1 and 2 = 2 or 3 = 3")
        node = parser.parseCondition()
        self.assertIsInstance(node, LogicalOperator)
        node = cast(LogicalOperator, node)
        self.assertEqual(node.operator.tokenType, TOKENS.T_OR)
        nodeLeft = node.leftOperand
        nodeRight = node.rightOperand
        self.assertIsInstance(nodeLeft, LogicalOperator)
        nodeLeft = cast(LogicalOperator, nodeLeft)
        self.assertEqual(nodeLeft.operator.tokenType, TOKENS.T_AND)
        self.assertIsInstance(nodeRight, RelationalOperator)
        nodeRight = cast(RelationalOperator, nodeRight)
        self.assertEqual(nodeRight.operator.tokenType, TOKENS.T_EQU)
        self.assertEqual(node.evaluate(), True)

    def testParseConditionFalse(self):
        parser = self.getParser("1 < 1 and 2 = 2 or 3 != 3")
        node = parser.parseCondition()
        self.assertIsInstance(node, LogicalOperator)
        node = cast(LogicalOperator, node)
        self.assertEqual(node.operator.tokenType, TOKENS.T_OR)
        nodeLeft = node.leftOperand
        nodeRight = node.rightOperand
        self.assertIsInstance(nodeLeft, LogicalOperator)
        nodeLeft = cast(LogicalOperator, nodeLeft)
        self.assertEqual(nodeLeft.operator.tokenType, TOKENS.T_AND)
        self.assertIsInstance(nodeRight, RelationalOperator)
        nodeRight = cast(RelationalOperator, nodeRight)
        self.assertEqual(nodeRight.operator.tokenType, TOKENS.T_NEQU)
        self.assertEqual(node.evaluate(), False)

    def testLogicalPrecedence(self):
        parser = self.getParser("1 = 1 or 2 = 2 and 5 = 3")
        node = parser.parseCondition()
        self.assertEqual(node.evaluate(), True)
        parser = self.getParser("{1 = 1 or 2 = 2} and 5 = 3")
        node = parser.parseCondition()
        self.assertEqual(node.evaluate(), False)

    def testProgramParse(self):
        with open("test/critter1.crtr", "r", encoding="utf-8") as file:
            lines = file.readlines()
        lineContent = lines[8:]
        content = "".join(lineContent)
        parser = self.getParser(content)
        program = parser.parse()
        self.assertEqual(13, len(program.getRules()))

        # POSTURE != 17 --> POSTURE := 17; // we are species 17!
        rule = program.rules[0]
        condition = rule.condition
        self.assertIsInstance(condition, RelationalOperator)
        commandBlock = rule.commands
        update = rule.commands[0]
        self.assertIsInstance(update, Update)
        update = cast(Update, update)
        self.assertEqual(update.source.evaluate(), 17)
        memNode = update.destination
        self.assertIsInstance(memNode, MemNode)
        self.assertEqual(memNode.getValue().evaluate(), 6)
        prettyPrint = "POSTURE != 17 --> \n     POSTURE := 17\n     ;\n"
        self.assertEqual(prettyPrint, str(rule))

        # {ENERGY > SIZE * 400 and SIZE < 7} --> grow;
        rule = program.rules[2]
        condition = rule.condition
        self.assertIsInstance(condition, LogicalOperator)
        condition = cast(LogicalOperator, condition)
        operator = condition.operator
        self.assertEqual(operator.tokenType, TOKENS.T_AND)
        leftOperand = condition.leftOperand
        self.assertIsInstance(leftOperand, RelationalOperator)
        leftOperand = cast(RelationalOperator, leftOperand)
        self.assertEqual(leftOperand.operator.tokenType, TOKENS.T_GREAT)
        leftOperand = leftOperand.leftOperand
        self.assertIsInstance(leftOperand, MemNode)
        leftOperand = cast(MemNode, leftOperand)
        self.assertEqual(leftOperand.getValue().evaluate(), 4)
        command = rule.commands[0]
        self.assertIsInstance(command, Action)
        command = cast(Action, command)
        self.assertEqual(command.actionType.tokenType, TOKENS.T_GROW)
        prettyPrint = "ENERGY > SIZE * 400 and SIZE < 7 --> \n     grow\n     ;\n"
        self.assertEqual(prettyPrint, str(rule))

        # {ahead[2] < -10 or random[20] = 0} and ahead[1] = 0 --> forward;
        rule = program.rules[5]
        condition = rule.condition
        self.assertIsInstance(condition, LogicalOperator)
        condition = cast(LogicalOperator, condition)
        operand = condition.leftOperand
        self.assertIsInstance(operand, LogicalOperator)
        operand = cast(LogicalOperator, operand)
        operator = operand.operator
        self.assertIsInstance(operator, TokenLexeme)
        self.assertEqual(operator.tokenType, TOKENS.T_OR)
        command = rule.commands[0]
        self.assertIsInstance(command, Action)
        command = cast(Action, command)
        self.assertEqual(command.actionType.tokenType, TOKENS.T_FORWARD)
        prettyPrint = "{ahead[2] < -10 or random[20] = 0} and ahead[1] = 0 --> \n     forward\n     ;\n"
        self.assertEqual(prettyPrint, str(rule))

        # 1 = 1 --> wait; // mostly soak up the rays
        rule = program.rules[12]
        condition = rule.condition
        self.assertIsInstance(condition, RelationalOperator)
        condition = cast(RelationalOperator, condition)
        self.assertEqual(condition.operator.tokenType, TOKENS.T_EQU)
        command = rule.commands[0]
        self.assertIsInstance(command, Action)
        command = cast(Action, command)
        self.assertEqual(command.actionType.tokenType, TOKENS.T_WAIT)
        prettyPrint = "1 = 1 --> \n     wait\n     ;\n"
        self.assertEqual(prettyPrint, str(rule))
