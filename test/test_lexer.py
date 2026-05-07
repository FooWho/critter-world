from __future__ import annotations

import unittest
from typing import Iterator, List
from lexer import Lexer
from schemas import Token, TOKENS

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

    KEYWORDS = {
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

    def testKeywords(self):
        lexer = Lexer()
        tmpStr = ''
        for element in self.KEYWORDS.values():
            tmpStr += element + ' '

        tokens: List[Token] = list(lexer.tokenize(tmpStr))
        self.assertEqual(len(tokens), len(self.KEYWORDS) + 1)
        self.assertEqual(tokens[len(tokens)-1].tokenType.name, TOKENS.T_EOF.name)
        for i, element in enumerate(self.KEYWORDS.keys()):
            self.assertEqual(tokens[i].tokenType.name, element)
    
    def testOperators(self):
        lexer = Lexer()
        tmpStr = ''
