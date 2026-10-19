import re
from dataclasses import dataclass

# List of tuples (token_type_name, regex pattern)
Tokens = [
    # --- Original keywords ---
    ("ASSIGN", r"assign\b"), ("PLUS", r"plus\b"), ("MINUS", r"minus\b"),
    ("MULTIPLY", r"times\b"), ("DIVIDE", r"divide\b"), ("PRINT", r"print\b"),
    ("IF", r"if\b"), ("ELSE", r"else\b"), ("WHILE", r"while\b"),
    ("GT_KEYWORD", r"gt\b"), ("LT_KEYWORD", r"lt\b"),
    
    # Music function keywords
    ("COMPOSE", r"compose\b"), ("PLAY", r"play\b"), ("PAUSE", r"pause\b"),

    # Music config keywords
    ("BPM", r"bpm\b"),
    ("DENSITY", r"density\b"),
    ("BRIGHTNESS", r"brightness\b"),
    ("SCALE", r"scale\b"),
    ("MUTE_DRUMS", r"mute_drums\b"),
    ("MUTE_BASS", r"mute_bass\b"),
    ("TRUE", r"true\b"),
    ("FALSE", r"false\b"),
    ("AUTO", r"auto\b"),
    ("LOW", r"low\b"),
    ("HIGH", r"high\b"),

    # Operators
    ("ID", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("NUMBER", r"\d+"), ("STRING", r'"[^"]*?"'),
    ("EQ_EQ", r"=="), ("GT", r">"), ("LT", r"<"),
    ("EQ", r"="), ("PLUS_SYM", r"\+"), ("MINUS_SYM", r"-"),
    ("MULTIPLY_SYM", r"\*"), ("SLASH_SYM", r"/"),
    ("LPAREN", r"\("), ("RPAREN", r"\)"), ("LBRACE", r"\{"), ("RBRACE", r"\}"),
    ("SEMI", r";"), ("NEWLINE", r"\n"), ("COMMENT", r"#[^\n]*"),
    ("SKIP", r"[ \t]+"), ("MISMATCH", r"."),
]

# Combine all patterns into one giant regex with named groups. group = token type.
MATCH_RE = re.compile("|".join(f"(?P<{t}>{p})" for t, p in Tokens))

@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int

class Lexer:
    def __init__(self, text: str):
        self.text = text

    def tokenizer(self):
        line, line_start = 1, 0
        col = 1 # Initialize col
        for m in MATCH_RE.finditer(self.text): 
            kind = m.lastgroup  # m.lastgroup returns the type and stores in kind
            value = m.group()   # m.group gets the value
            col = m.start() - line_start + 1    

            # if token is NEWLINE, add line count, reset column tracking, and continue
            if kind == "NEWLINE":
                line += 1; line_start = m.end(); continue

            # ignores skip and comment
            if kind in ("SKIP", "COMMENT"): continue

            # invalid syntax
            if kind == "MISMATCH":
                raise SyntaxError(f"Unexpected token '{value}' at {line}:{col}")
            yield Token(kind, value, line, col) 
        yield Token("EOF", "", line, col)   # EOF sentinel