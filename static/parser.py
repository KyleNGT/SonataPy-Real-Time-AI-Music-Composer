from ast_nodes import *
from tokenizer import Token

class Parser:
    def __init__(self, tokens): # List of tokens and current index of token being processed
        self.tokens = list(tokens); self.token_idx = 0  # Parser's current token index


    # CORE NAVIGATION METHODS
    # Get the current token else return EOF
    def current_token(self):    
        return self.tokens[self.token_idx] if self.token_idx < len(self.tokens) else self.tokens[-1]

    # Consume the current token and advance to the next one
    def eat(self, token_type=None): 
        token = self.current_token()                # Get current token via current_token()

        if token_type and token.type != token_type: # Terminate program if token type is invalid
            raise SyntaxError(f"Line {token.line}, Col {token.col}: Expected '{token_type}', got '{token.type}'")
        self.token_idx += 1; return token


    # EXPRESSION PARSING METHODS
    # Parse the term if NUMBER, ID(variables), or STRING
    def parse_term(self):
        token = self.current_token()                                                        # Get current token via current_token()
        if token.type == "NUMBER": self.eat("NUMBER"); return NumberNode(token.value)       # If token is a number, return int equivalent of the token
        elif token.type == "ID": self.eat("ID"); return VarNode(token.value)
        elif token.type == "STRING": self.eat("STRING"); return StringNode(token.value)
        
        # --- NEW: Parse value keywords as StringNodes ---
        elif token.type in ("LOW", "HIGH", "AUTO", "TRUE", "FALSE"):
            self.eat(token.type)
            return StringNode(f'"{token.value}"') # Store 'low' as "low"
            
        else: raise SyntaxError(f"Unexpected term '{token.value}' at line {token.line}")

    # Parse an expression to binary operator node
    def parse_expression(self):
        node = self.parse_term()    # Parse the left term

        while self.current_token().type in ("PLUS", "MINUS", "MULTIPLY", "DIVIDE"):
            op_token = self.eat()   # Consume operator token
            op_map = {"PLUS": "plus", "MINUS": "minus", "MULTIPLY": "times", "DIVIDE": "divide"}   
            right = self.parse_term(); node = BinOpNode(node, op_map[op_token.type], right)    
        return node

    # Parse comparison expressions
    def parse_comparison(self):
        left = self.parse_expression()  # Parse left expression
        op_token = self.current_token() # Get current token

        # Check if the token is a comparison operator
        if op_token.type in ("EQ_EQ", "GT_KEYWORD", "LT_KEYWORD"):
            self.eat(op_token.type)
            op_map = {"EQ_EQ": "eq_eq", "GT_KEYWORD": "gt", "LT_KEYWORD": "lt"}
            right = self.parse_expression()
            return ComparisonNode(left, op_map[op_token.type], right)
        return left # If no comparison operator, return left expression as is

    # STATEMENT PARSING METHODS
    # Parse a block of statements enclosed in braces
    def parse_block(self):
        self.eat("LBRACE")  # Consume and checks for '{'
        statements = []     # Initialize empty list for statements

        # Parse statements until the closing brace is found
        while self.current_token().type != "RBRACE":
            if self.token_idx >= len(self.tokens): raise SyntaxError("Unexpected end of input inside block.") 

            if self.current_token().type in ("SEMI", "NEWLINE"): self.eat(); continue   
            statements.append(self.parse_statement())                                 
        self.eat("RBRACE")  # Consume and checks for '}'
        return BlockNode(statements)

    # Parse an if statement
    def parse_if_statement(self):
        self.eat("IF"); self.eat("LPAREN")                    
        condition = self.parse_comparison(); self.eat("RPAREN") 
        then_body = self.parse_block(); else_body = None      

        # Check for optional 'else' block
        if self.current_token().type == "ELSE":                 
            self.eat("ELSE"); else_body = self.parse_block()  
        return IfNode(condition, then_body, else_body)       

    # Parse a while statement
    def parse_while_statement(self):
        self.eat("WHILE"); self.eat("LPAREN")                    
        condition = self.parse_comparison(); self.eat("RPAREN")
        body = self.parse_block()                              
        return WhileNode(condition, body)                    

    # Parse an assignment statement
    def parse_assign_statement(self):
        var_token = self.eat("ID"); self.eat("ASSIGN")  
        expr = self.parse_expression()                  
        return AssignNode(var_token.value, expr)       

    # Parse a print statement
    def parse_print_statement(self):
        self.eat("PRINT"); expr = self.parse_expression(); return PrintNode(expr)   

    # Parse a compose statement
    def parse_compose_statement(self):
        self.eat("COMPOSE")          
        expr = self.parse_expression()  
        return ComposeNode(expr)       

    def parse_bpm_statement(self):
        self.eat("BPM")
        value_node = self.parse_expression() 
        self.eat("SEMI")
        return SetBPMNode(value_node)

    def parse_density_statement(self):
        self.eat("DENSITY")
        value_node = self.parse_expression() # Expects LOW, HIGH, or AUTO
        self.eat("SEMI")
        return SetDensityNode(value_node)

    def parse_brightness_statement(self):
        self.eat("BRIGHTNESS")
        value_node = self.parse_expression() # Expects LOW, HIGH, or AUTO
        self.eat("SEMI")
        return SetBrightnessNode(value_node)
        
    def parse_scale_statement(self):
        self.eat("SCALE")
        value_node = self.parse_expression() # Expects a STRING or a VarNode
        self.eat("SEMI")
        return SetScaleNode(value_node)

    def parse_mute_drums_statement(self):
        self.eat("MUTE_DRUMS")
        value_node = self.parse_expression() # Expects TRUE or FALSE
        self.eat("SEMI")
        return MuteDrumsNode(value_node)

    def parse_mute_bass_statement(self):
        self.eat("MUTE_BASS")
        value_node = self.parse_expression() # Expects TRUE or FALSE
        self.eat("SEMI")
        return MuteBassNode(value_node)
        

    # Decides which statement to parse based on the current token
    def parse_statement(self):
        token_type = self.current_token().type  # Get current token type

        # Decide which statement to parse based on the current token type
        if token_type == "ID" and self.tokens[self.token_idx + 1].type == "ASSIGN":
            node = self.parse_assign_statement()   
            self.eat("SEMI")                        
            return node                             
        elif token_type == "PRINT":                 
            node = self.parse_print_statement()   
            self.eat("SEMI")                       
            return node
        elif token_type == "IF":                  
            return self.parse_if_statement()
        elif token_type == "WHILE":                 
            return self.parse_while_statement()
        elif token_type == "COMPOSE":               
            node = self.parse_compose_statement()
            self.eat("SEMI")                        
            return node
        elif token_type == "PLAY":                 
            self.eat("PLAY"); self.eat("SEMI")
            return PlayNode()
        elif token_type == "PAUSE":                 
            self.eat("PAUSE"); self.eat("SEMI")
            return PauseNode()
        elif token_type == "BPM":
            return self.parse_bpm_statement()
        elif token_type == "DENSITY":
            return self.parse_density_statement()
        elif token_type == "BRIGHTNESS":
            return self.parse_brightness_statement()
        elif token_type == "SCALE":
            return self.parse_scale_statement()
        elif token_type == "MUTE_DRUMS":
            return self.parse_mute_drums_statement()
        elif token_type == "MUTE_BASS":
            return self.parse_mute_bass_statement()
            
        # If no valid statement is found, raise a syntax error
        else:
            token = self.current_token()
            raise SyntaxError(f"Unexpected token '{token.type}' at line {token.line}")

    # MAIN PARSING METHOD
    # Parse the entire list of tokens into AST nodes
    def parse(self):
        nodes = []                                                  
        while self.current_token().type != "EOF":                   
            if self.current_token().type in ("NEWLINE", "SEMI"):   
                self.eat()
                continue
            nodes.append(self.parse_statement())                   
        return nodes   