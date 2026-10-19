from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware 
from pydantic import BaseModel 

from tokenizer import Lexer
from parser import Parser
from interpreter import Interpreter


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

# Allows frontend (script.js) to send requests to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins, adjust for production
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# This defines the shape of the data we expect from script.js
class CodeInput(BaseModel):
    code: str

# Create a single, reusable interpreter instance
interpreter_instance = Interpreter()



#NEW API Endpoint
@app.post("/interpret")
async def run_interpreter(data: CodeInput):
    """
    Receives a string of custom language code, runs it through
    the interpreter, and returns the compiled config dictionary.
    """
    try:
        #Tokenize
        lexer = Lexer(data.code)
        tokens = list(lexer.tokenizer())
        
        # Parse
        parser = Parser(tokens)
        ast_nodes = parser.parse()
        
        # Interpret
        result = interpreter_instance.run_program(ast_nodes)
        
        # Return
        return result

    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
        # If anything goes wrong, return a 400 error
        raise HTTPException(
            status_code=400, 
            detail=f"Interpreter Error: {str(e)}"
        )
    except Exception as e:
        # Catch any other unexpected server errors
        raise HTTPException(
            status_code=500, 
            detail=f"Internal Server Error: {str(e)}"
        )

@app.get("/")
def get_splash():
    return FileResponse(str(BASE_DIR / "splash_screen.html"))

app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)