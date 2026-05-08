from __future__ import annotations

import unittest
from typing import Iterator, List
from lexer import Lexer
from schemas import Token, TOKENS, CritterParseError

class TestLexer(unittest.TestCase):

    SAMPLES = { 
        TOKENS.T_MEMSIZE.name: 'MEMSIZE',
        TOKENS.T_DEFENSE.name: 'DEFENSE',
        TOKENS.T_OFFENSE.name: 'OFFENSE',
        TOKENS.T_SIZE.name: 'SIZE',
        TOKENS.T_ENERGY.name: 'ENERGY',
        TOKENS.T_PASS.name: 'PASS',
        TOKENS.T_POSTURE.name: 'POSTURE',
        TOKENS.T_AND.name: 'and',
        TOKENS.T_OR.name: 'or',
        TOKENS.T_SMELL.name: 'smell',
        TOKENS.T_NEARBY.name: 'nearby',
        TOKENS.T_AHEAD.name: 'ahead',
        TOKENS.T_RANDOM.name: 'random',
        TOKENS.T_WAIT.name: 'wait',
        TOKENS.T_FORWARD.name: 'forward',
        TOKENS.T_BACKWARD.name: 'backward',
        TOKENS.T_LEFT.name: 'left',
        TOKENS.T_RIGHT.name: 'right',
        TOKENS.T_EAT.name: 'eat',
        TOKENS.T_ATTACK.name: 'attack',
        TOKENS.T_BUD.name: 'bud',
        TOKENS.T_MEM.name: 'mem',
        TOKENS.T_STAR.name: '*',
        TOKENS.T_PLUS.name: '+',
    }



    def testKeywords(self):
        lexer = Lexer()
        keywords = {
            TOKENS.T_MEMSIZE.name: 'MEMSIZE',
            TOKENS.T_DEFENSE.name: 'DEFENSE',
            TOKENS.T_OFFENSE.name: 'OFFENSE',
            TOKENS.T_SIZE.name: 'SIZE',
            TOKENS.T_ENERGY.name: 'ENERGY',
            TOKENS.T_PASS.name: 'PASS',
            TOKENS.T_POSTURE.name: 'POSTURE',
            TOKENS.T_AND.name: 'and',
            TOKENS.T_OR.name: 'or',
            TOKENS.T_SMELL.name: 'smell',
            TOKENS.T_NEARBY.name: 'nearby',
            TOKENS.T_AHEAD.name: 'ahead',
            TOKENS.T_RANDOM.name: 'random',
            TOKENS.T_WAIT.name: 'wait',
            TOKENS.T_FORWARD.name: 'forward',
            TOKENS.T_BACKWARD.name: 'backward',
            TOKENS.T_LEFT.name: 'left',
            TOKENS.T_RIGHT.name: 'right',
            TOKENS.T_EAT.name: 'eat',
            TOKENS.T_ATTACK.name: 'attack',
            TOKENS.T_BUD.name: 'bud',
            TOKENS.T_GROW.name: 'grow',
            TOKENS.T_SERVE.name: 'serve',
        }
        tmpStr = ' '.join(keywords.values())
        tokens: List[Token] = list(lexer.tokenize(tmpStr))
        
        self.assertEqual(len(tokens), len(keywords) + 1)
        self.assertEqual(tokens[-1].tokenType.name, TOKENS.T_EOF.name)
        for i, element in enumerate(keywords.keys()):
            self.assertEqual(tokens[i].tokenType.name, element)
    
    def testOperators(self):
        lexer = Lexer()
        operator_map = {
            TOKENS.T_ASSIGN: ':=',
            TOKENS.T_LEQU: '<=',
            TOKENS.T_GEQU: '>=',
            TOKENS.T_NEQU: '!=',
            TOKENS.T_LESS: '<',
            TOKENS.T_GREAT: '>',
            TOKENS.T_EQU: '=',
            TOKENS.T_COMM: '-->',
            TOKENS.T_PLUS: '+',
            TOKENS.T_MINUS: '-',
            TOKENS.T_STAR: '*',
            TOKENS.T_DIV: '/',
            TOKENS.T_MOD: 'mod',
        }
        tmpStr = ' '.join(operator_map.values())
        tokens: List[Token] = list(lexer.tokenize(tmpStr))
        
        self.assertEqual(len(tokens), len(operator_map) + 1)
        self.assertEqual(tokens[-1].tokenType, TOKENS.T_EOF)
        for i, expected_token in enumerate(operator_map.keys()):
            self.assertEqual(tokens[i].tokenType, expected_token)

    def testPunctuation(self):
        lexer = Lexer()
        punct_map = {
            TOKENS.T_L_PAREN: '(',
            TOKENS.T_R_PAREN: ')',
            TOKENS.T_L_BRACKET: '[',
            TOKENS.T_R_BRACKET: ']',
            TOKENS.T_L_BRACE: '{',
            TOKENS.T_R_BRACE: '}',
            TOKENS.T_SEMICOLON: ';',
        }
        tmpStr = ' '.join(punct_map.values())
        tokens: List[Token] = list(lexer.tokenize(tmpStr))
        
        self.assertEqual(len(tokens), len(punct_map) + 1)
        self.assertEqual(tokens[-1].tokenType, TOKENS.T_EOF)
        for i, expected_token in enumerate(punct_map.keys()):
            self.assertEqual(tokens[i].tokenType, expected_token)

    def testNumbers(self):
        lexer = Lexer()
        tmpStr = "0 123 9999"
        tokens: List[Token] = list(lexer.tokenize(tmpStr))
        
        self.assertEqual(len(tokens), 4) # 3 numbers + EOF
        for i in range(3):
            self.assertEqual(tokens[i].tokenType, TOKENS.T_NUMBER)
            
        self.assertEqual(tokens[0].lexeme, "0")
        self.assertEqual(tokens[1].lexeme, "123")
        self.assertEqual(tokens[2].lexeme, "9999")

    def testLineAndColumnTracking(self):
        lexer = Lexer()
        tmpStr = "mem[0]\n:= 5\nwait;"
        tokens: List[Token] = list(lexer.tokenize(tmpStr))
        
        expected_positions = [
            (0, 0, TOKENS.T_MEM),
            (0, 3, TOKENS.T_L_BRACKET),
            (0, 4, TOKENS.T_NUMBER),
            (0, 5, TOKENS.T_R_BRACKET),
            (1, 0, TOKENS.T_ASSIGN),
            (1, 3, TOKENS.T_NUMBER),
            (2, 0, TOKENS.T_WAIT),
            (2, 4, TOKENS.T_SEMICOLON),
            (2, 5, TOKENS.T_EOF)
        ]
        
        self.assertEqual(len(tokens), len(expected_positions))
        for i, (exp_line, exp_col, exp_tok) in enumerate(expected_positions):
            self.assertEqual(tokens[i].tokenType, exp_tok)
            self.assertEqual(tokens[i].line, exp_line)
            self.assertEqual(tokens[i].column, exp_col)

    def testCommentsAndWhitespaceSkipping(self):
        lexer = Lexer()
        tmpStr = "ahead[1] // checking ahead\n * 5"
        tokens: List[Token] = list(lexer.tokenize(tmpStr))
        
        # The '*' token should be recorded as being on line 1, column 1
        self.assertEqual(tokens[4].tokenType, TOKENS.T_STAR)
        self.assertEqual(tokens[4].line, 1)

    def testMismatchError(self):
        lexer = Lexer()
        with self.assertRaises(CritterParseError):
            list(lexer.tokenize("mem[0] $ 5"))
