from __future__ import annotations
from typing import ClassVar, Iterable, Iterator, TYPE_CHECKING
from schemas import Token, CritterParseError, TokenLexeme, TermTuple, FactorTuple, TOKENS, SET_RELOPS, SET_ADDOPS, SET_MULOPS
from abstractSyntaxTree import Program, Rule, Condition, Command, Conjunction, Relation, Expr, Term, Factor, Number

class Parser():
    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens: Iterator[Token] = tokens
        self.current: Token|None = next(tokens, None)

    def getToken(self) -> Token|None:
        token: Token|None = self.current
        self.current = next(self.tokens, None)
        return token
    
    def peek(self) -> Token|None:
        return self.current
    
    def parseProgram(self) -> Program:
        program: Program = Program()

        token = self.getToken()

        while token :
            program.addRule(self.parseRule(token))
            self.getToken()

        return program
    
    def parseRule(self, token: Token) -> Rule:
        condition: Condition
        command: Command

        condition = self.parseCondition(token)
        command = self.parseCommand()

        return Rule(condition, command)
    
    def parseCondition(self, token: Token) -> Condition:
        condition: Condition = Condition()
        conjunctions: list[Conjunction] = []
        conjunction: Conjunction = Conjunction()

        # A Condition may have a list of conjunctions, for now, we will assume 1 and fix later
        conjunction = self.parseConjunction(token)

        return condition
    
    
    def parseCommand(self) -> Command:
        command: Command = Command()

        return command
    
    def parseConjunction(self, token: Token) -> Conjunction:
        conjunction: Conjunction = Conjunction()
        relation: Relation = Relation()

        # A Conjunction may have a list of relations,  for now assume one and fix later
        relation = self.parseRelation(token)

        print(f'{str(relation)}')

        return conjunction
    
    def parseRelation(self, token: Token) -> Relation:
        leftExpression: Expr
        relOp: TokenLexeme
        rightExpression: Expr

        leftExpression = self.parseExpression(token)
        nextToken: Token|None = self.getToken()
        if nextToken:
            token = nextToken
        else:
            raise CritterParseError('Error: Exprected relational operator in expression, but got "None"')
        relOp = TokenLexeme(token.tokenType, token.lexeme)
        nextToken = self.getToken()
        if nextToken:
            token = nextToken
        else:
            raise CritterParseError('Error: Exprected relational operator in expression, but got "None"')
        rightExpression = self.parseExpression(token)     

        relation = Relation(leftExpression, rightExpression, relOp)
        print(f'{str(relation)}')
        return Relation(leftExpression, rightExpression, relOp)
    
    def parseExpression(self, token: Token) -> Expr:
        expression: Expr = Expr()

        expression.setTerms(self.parseTerms(token))

        return expression
    
    def parseTerms(self, token: Token) -> list[TermTuple]:
        terms: list[TermTuple] = []
  
        while token.tokenType not in SET_RELOPS | {TOKENS.T_COMM}:
            if token == self.peek():
                self.getToken()
            addOp: TokenLexeme = TokenLexeme(TOKENS.T_NONE, '')
            if token.tokenType in {TOKENS.T_PLUS, TOKENS.T_MINUS}:
                addOp = TokenLexeme(token.tokenType, token.lexeme)
                tmpToken = self.getToken()
                if tmpToken:
                    token = tmpToken
            factorTupleList = self.parseFactors(token)
            term = Term(factorTupleList)
            term.__repr__()
            terms.append(TermTuple(addOp, term))
            tmpToken = self.peek()
            if tmpToken:
                token = tmpToken
            else:
                raise CritterParseError('Error!')
        
        return terms
    
    def parseFactors(self, token: Token) -> list[FactorTuple]:
        number: Number
        mulOp: TokenLexeme
        factors:list[FactorTuple] = []

        while token.tokenType not in SET_RELOPS | SET_ADDOPS:
            if token == self.peek():
                self.getToken()
            mulOp = TokenLexeme(TOKENS.T_NONE, '')
            if token.tokenType in SET_MULOPS:
                mulOp = TokenLexeme(token.tokenType, token.lexeme)






        mulOp = TokenLexeme(TOKENS.T_NONE, '')
        number = self.parseNumber(token)
        return [FactorTuple(mulOp, number)]
    
    def parseNumber(self, token: Token) -> Number:
        num: Number

        if token.tokenType != TOKENS.T_NUMBER:
            raise CritterParseError('Error!')
        else:    
            return Number(TokenLexeme(token.tokenType, token.lexeme))
    


