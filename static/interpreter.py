from ast_nodes import *

class Interpreter:
    def __init__(self):
        self.variables = {}
        self.music_config = {}
        self.prompts = []

    def run_program(self, ast_nodes):
        """
        Main entry point. Runs the list of AST nodes
        and returns the compiled config.
        """
        # Clear old config from previous runs
        self.variables = {}
        self.music_config = {}
        self.prompts = []

        # Run the interpreter on all statements
        for node in ast_nodes:
            self.eval(node)
            
        # Return the final compiled config
        return {
            "config": self.music_config,
            "prompts": self.prompts
        }

    def eval(self, node):
        if isinstance(node, NumberNode):            # If node is a number
            return node.value

        elif isinstance(node, StringNode):          # If node is a string
            return node.value

        elif isinstance(node, VarNode):             # Read variable value
            if node.name not in self.variables:     # Check if variable is defined
                raise NameError(f"Variable '{node.name}' is not defined.")
            return self.variables[node.name]        # Return variable value to caller

        elif isinstance(node, BinOpNode):           # If node is a binary operation
            left, right = self.eval(node.left), self.eval(node.right)
            if isinstance(left, str) or isinstance(right, str): # Prevent arithmetic on strings
                raise TypeError("Arithmetic only valid on numbers.")
            if node.op == "plus":
                return left + right
            elif node.op == "minus":
                return left - right
            elif node.op == "times":
                return left * right
            elif node.op == "divide":
                if right == 0:
                    raise ZeroDivisionError("Cannot divide by zero.")
                return left / right

        elif isinstance(node, AssignNode):          # Variable Assignment and storage
            value = self.eval(node.expr)
            self.variables[node.var_name] = value

        elif isinstance(node, PrintNode):           # Print statement    
            print(self.eval(node.expr)) # This will print to your backend console

        elif isinstance(node, ComparisonNode):      # Comparison operations
            left, right = self.eval(node.left), self.eval(node.right)
            if node.op == "eq_eq":
                return left == right
            elif node.op == "gt":
                return left > right
            elif node.op == "lt":
                return left < right

        elif isinstance(node, BlockNode):           # Block of statements
            for stmt in node.statements:
                self.eval(stmt)

        elif isinstance(node, IfNode):              # If statement
            if self.eval(node.condition):
                self.eval(node.then_body)
            elif node.else_body:
                self.eval(node.else_body)

        elif isinstance(node, WhileNode):           # While loop
            while self.eval(node.condition):
                self.eval(node.body)

        elif isinstance(node, SetBPMNode):
            self.music_config['bpm'] = self.eval(node.value)

        elif isinstance(node, SetScaleNode):
            scale_val = self.eval(node.value)
            # Use "SCALE_UNSPECIFIED" for "auto"
            if scale_val.lower() == "auto":
                self.music_config['scale'] = "SCALE_UNSPECIFIED"
            else:
                self.music_config['scale'] = scale_val

        elif isinstance(node, MuteDrumsNode):
            value = self.eval(node.value) # Will be "true" or "false"
            self.music_config['mute_drums'] = (value.lower() == 'true')
        
        elif isinstance(node, MuteBassNode):
            value = self.eval(node.value) # Will be "true" or "false"
            self.music_config['mute_bass'] = (value.lower() == 'true')

        elif isinstance(node, SetDensityNode):
            value = self.eval(node.value) # Will be "low", "high", or "auto"
            if value == "low":
                self.music_config['density'] = 0.2
            elif value == "high":
                self.music_config['density'] = 0.7
            # If "auto", we simply don't add it to the config

        elif isinstance(node, SetBrightnessNode):
            value = self.eval(node.value) # Will be "low", "high", or "auto"
            if value == "low":
                self.music_config['brightness'] = 0.2
            elif value == "high":
                self.music_config['brightness'] = 0.7
        elif isinstance(node, ComposeNode):
            # Parse the prompt string ("piano:1.5, drums:1.0")
            raw_string = self.eval(node.value)
            parsed_prompts = []
            
            if not raw_string:
                self.prompts = []
                return

            for part in raw_string.split(','):
                part = part.strip()
                if not part:
                    continue
                
                if ':' in part:
                    try:
                        text, weight_str = part.rsplit(':', 1)
                        weight = float(weight_str.strip())
                        parsed_prompts.append({'text': text.strip(), 'weight': weight})
                    except ValueError:
                        # Handle case like "hello:" or "hello:abc"
                        parsed_prompts.append({'text': part, 'weight': 1.0})
                else:
                    parsed_prompts.append({'text': part, 'weight': 1.0})
            
            self.prompts = parsed_prompts
        
        elif isinstance(node, PlayNode):
            pass

        elif isinstance(node, PauseNode):
            pass

        else:
            raise TypeError(f"Unknown node: {type(node)}")