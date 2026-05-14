from __future__ import annotations
import random, math
from abstractSyntaxTree import ASTNode, Program, CommandBlock

class Mutator:

   def __init__(self, mutationProbability: float = 0.0) -> None:
        self.mutationProbability = mutationProbability

   def getWeightedRandom(self):
      loc = random.choice([-1, 1])
      beta = 1.5
      variation = random.expovariate(1/beta) * random.choice([-1, 1])
      result = int(round(loc + variation))
      if result < -10: result = -1
      if result > 10: result = 1
      if result == 0: result = random.choice([-2, -1, 1, 2])
      return result

   def mutate(self, program: Program, mutations: int) -> Program:
      """
        From the original:
        1. Remove: The node, along with all its descendants, is removed. If the parent of the node being removed
           needs a replacement child, one of the node's direct children of the correct kind is randomly selected. 
           For example, a rule node is simply removed, whereas a binary operation node would be replaced with either
           its left or its right child. Note that a legal program must contain at least one rule.
        2. Swap: The order of two children of the node is switched. For example, this allows swapping the positions 
           of two rules, or changing a - b to b - a.
        3. Replace: The node and its descendants are replaced with a randomly selected subtree of the right kind.
           Randomly selected subtrees are chosen from somewhere in the current AST. The entire AST subtree
           rooted at the selected node is cloned (deep-copied).
        4. Transform: The node is replaced with a random, newly created node of the same kind (for example,
           replacing attack with eat, or + with *), but its children remain the same. Literal integer constants are
           randomly adjusted up or down by the value of java.lang.Integer.MAX_VALUE/r.nextInt(), where
           legal, assuming that r is an object of class java.util.Random.
        5. Insert: A newly created node is inserted as the parent of the mutated node. The old parent of the
           mutated node becomes the parent of the inserted node, and the mutated node becomes a child of the
           inserted node. If the inserted node requires more than one child, the children that are not the original
           node are copies of randomly chosen nodes of the right kind from the entire rule set.
        6. Duplicate: For nodes with a variable number of children, a randomly selected subtree of the right type
           (as in Replace mutations) is appended to the end of the list of children. This applies to the root node,
           where a new rule can be added, and also to command nodes, where the sequence of updates can be
           extended with another update.

        On rule 4, Transform, I am going to make a modification to the original spec. They want to shift integer
        literals up or down by a random value that could be large but is going to be heavily clustered around
        [-1, 1]. My get_weighted_random() method should give a distribution heavily weighted to -1 and 1, with
        tails that fall off rapidly. I am not going to allow a zero. If the mutator decides we are going to change,
        we won't decide to 'change by 0'. I am going to restrict change to [-10, 10].
      """

      for i in range(0, mutations):
         mutation_type = random.choice([1, 2, 3, 4, 5, 6])
         match mutation_type:
            case 1:
               pass
            case 2:
               pass
            case 3:
               pass
            case 4:
               pass
            case 5:
               pass
            case 6:
               pass

      return Program()
   
   def countNodes(self, node: ASTNode):
      nodes = 0
      if not isinstance(node, (Program, CommandBlock)): nodes = 1 # Don't count the program itself or the CommandBlock, they are passthrough.
      for child in node:
         nodes += self.countNodes(child)
      return nodes
   
   def numberFaultInjector(self) -> None:
      pass
   
   """
   def mutateTransform(self, amount: int) -> None:
        self.value += amount
        self.number = TokenLexeme(TOKENS.T_NUMBER, str(self.value))
    
   def mutateInsert(self) -> ExpressionNode:
        unaryOperator = UnaryOperator(TokenLexeme(TOKENS.T_MINUS, '-'), self)
        return unaryOperator
   """
