from __future__ import annotations
from typing import ClassVar, Iterable, Iterator, TYPE_CHECKING
from schemas import Token, CritterParseError, TokenLexeme, TermTuple, FactorTuple, TOKENS, SET_RELOPS, SET_ADDOPS, SET_MULOPS, SET_SENSORS, SET_FACTOR_TERMINATORS, SET_FACTORS
from abstractSyntaxTree import Program, Rule, Condition, Command, Conjunction, Relation, Expr, Term, Factor, Number

class Parser():
    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens: Iterator[Token] = tokens
        self.current: Token = Token(TOKENS.T_NONE, '', 0, 0)
        tmp = next(self.tokens, None)
        if tmp:
            self.current = tmp

    def getToken(self) -> Token:
        token: Token = self.current
        tmp = next(self.tokens, None)
        if tmp:
            self.current = tmp
        return token
    
    def peek(self) -> Token:
        return self.current
    
    def parseProgram(self) -> Program:
        program: Program = Program()

        token = self.getToken()

        while token.tokenType != TOKENS.T_NONE:
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
    
        return conjunction
    
    def parseRelation(self, token: Token) -> Relation:
        leftExpression: Expr
        relOp: TokenLexeme
        rightExpression: Expr

        leftExpression = self.parseExpression(token)
        token = self.getToken()
        relOp = TokenLexeme(token.tokenType, token.lexeme)
        token = self.getToken()
        rightExpression = self.parseExpression(token)     

        relation = Relation(leftExpression, rightExpression, relOp)
        return Relation(leftExpression, rightExpression, relOp)
    
    def parseExpression(self, token: Token) -> Expr:
        expression: Expr = Expr()

        expression.setTerms(self.parseTerms(token))
        print(f'{expression}')
        return expression
    
    def parseTerms(self, token: Token) -> list[TermTuple]:
        terms: list[TermTuple] = []
  
        while token.tokenType not in SET_RELOPS | {TOKENS.T_COMM}:
            if token == self.peek():
                token = self.getToken()
            addOp: TokenLexeme = TokenLexeme(TOKENS.T_NONE, '')
            if token.tokenType in {TOKENS.T_PLUS, TOKENS.T_MINUS}:
                addOp = TokenLexeme(token.tokenType, token.lexeme)
                tmpToken = self.getToken()
                if tmpToken:
                    token = tmpToken
            factorTupleList = self.parseFactors(token)
            term = Term(factorTupleList)
            terms.append(TermTuple(addOp, term))
            tmpToken = self.peek()
            if tmpToken:
                token = tmpToken
            else:
                raise CritterParseError('Error!')
        
        return terms
    
    def parseFactors(self, token: Token) -> list[FactorTuple]:
        number: Number
        mulOp: TokenLexeme = TokenLexeme(TOKENS.T_NONE, '')
        factors:list[FactorTuple] = []

        while token.tokenType not in SET_FACTOR_TERMINATORS:
            if token is self.peek():
                # Our look-ahead says we are still here, advance the cursor
                token = self.getToken()
            # Parsing a factor, if it is not the first, it will have a leading mulOp, otherwise it is a syntax error
            if token.tokenType in SET_MULOPS and factors:
                # We are looking at a mulOp and this is not the first factor
                mulOp = TokenLexeme(token.tokenType, token.lexeme)
                token = self.getToken()
            if token.tokenType not in SET_FACTORS:
                raise CritterParseError(f'Error on line {token.line} at position {token.column}: Expected FACTOR. Read: {token.tokenType}:"{token.lexeme}"')
            # We should have a T_NUMBER, a T_MEM, a T_L_PAREN, a T_MINUS, or token ∈ {SET_SENSORS}
            match token.tokenType:
                case TOKENS.T_NUMBER:
                    number = self.parseNumber(token)
                    factors.append(FactorTuple(mulOp, number))
                    # Lookahead for next loop iteration
                    token = self.peek()
                case TOKENS.T_MEM:
                    pass
                case TOKENS.T_L_PAREN:
                    pass
                case TOKENS.T_MINUS:
                    pass
                case val if val in SET_SENSORS:
                    pass 
                case _:
                    raise CritterParseError(f'Error on line {token.line} at position {token.column}: Expected FACTOR. Read: {token.tokenType}:"{token.lexeme}"')         
                
        return factors
    
    def parseNumber(self, token: Token) -> Number:
        num: Number

        if token.tokenType != TOKENS.T_NUMBER:
            raise CritterParseError('Error!')
        else:    
            return Number(TokenLexeme(token.tokenType, token.lexeme))
    


