# Abstract Syntax Tree (AST) Node Definitions

class ASTNode: pass        # Base class for all AST nodes 

class AssignNode(ASTNode): # Assignment
    def __init__(self, var_name, expr): self.var_name = var_name; self.expr = expr

class PrintNode(ASTNode):   # Print statement
    def __init__(self, expr): self.expr = expr

class BinOpNode(ASTNode):   # Binary operation
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right

class NumberNode(ASTNode): # Number literal
    def __init__(self, value): self.value = int(value)

class VarNode(ASTNode):     # Variable reference
    def __init__(self, name): self.name = name

class StringNode(ASTNode): # String literal
    def __init__(self, value): self.value = value.strip('"')

class ComparisonNode(ASTNode):  # Comparison operation
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right

class BlockNode(ASTNode):   # Block of statements
    def __init__(self, statements): self.statements = statements

class IfNode(ASTNode):      # If statement
    def __init__(self, condition, then_body, else_body=None):
        self.condition = condition; self.then_body = then_body; self.else_body = else_body

class WhileNode(ASTNode):   # While statement
    def __init__(self, condition, body): self.condition = condition; self.body = body


class SetBPMNode(ASTNode):
    def __init__(self, value): self.value = value

class SetDensityNode(ASTNode):
    def __init__(self, value): self.value = value

class SetBrightnessNode(ASTNode):
    def __init__(self, value): self.value = value
    
class SetScaleNode(ASTNode):
    def __init__(self, value): self.value = value

class MuteDrumsNode(ASTNode):
    def __init__(self, value): self.value = value

class MuteBassNode(ASTNode):
    def __init__(self, value): self.value = value
    
class ComposeNode(ASTNode): 
    def __init__(self, value):
        self.value = value

class PlayNode(ASTNode):
    def __init__(self):
        pass

class PauseNode(ASTNode):
    def __init__(self):
        pass