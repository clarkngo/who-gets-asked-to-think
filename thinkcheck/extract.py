"""Pull the solution code out of a model response.

Rule (applied identically to every response):
1. Take every fenced code block tagged python/py, or untagged. Blocks tagged as another language
   (bash, text, output, ...) are ignored.
2. Parse each block on its own and skip any that aren't valid Python (e.g. REPL transcripts
   with >>> prompts, or snippets with "...").
3. Concatenate the valid blocks in order and keep only top-level imports, function and class
   definitions, and assignments that call nothing (constants). Demo code such as
   print(split_bill(100, 4, 20)), input(), loops and `if __name__ == "__main__":` blocks is
   dropped, so the tests judge the function rather than the example around it.
4. If the required function is defined more than once, the last definition wins (normal Python
   semantics), which matches "the final version" in a response that iterates.

Statuses: ok | no_code (no Python blocks) | unparseable (blocks, none valid) |
          no_function (valid code, but the required function isn't defined at top level)
"""
import ast
import re
from dataclasses import dataclass, field

FENCE = re.compile(r"```[ \t]*([A-Za-z0-9_+-]*)[^\n]*\n(.*?)```", re.S)
PYTHON_TAGS = {"", "python", "py", "python3"}
KEEP = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


@dataclass
class Extraction:
    status: str
    code: str = ""
    blocks_total: int = 0           # all fenced blocks
    blocks_python: int = 0          # python/untagged blocks
    blocks_parsed: int = 0          # python blocks that parsed
    definitions_of_function: int = 0
    dropped: dict = field(default_factory=dict)  # statement kind -> count


def _calls_something(node) -> bool:
    return any(isinstance(n, ast.Call) for n in ast.walk(node))


def extract(response: str, function: str) -> Extraction:
    blocks = FENCE.findall(response or "")
    python_blocks = [body for tag, body in blocks if tag.lower() in PYTHON_TAGS]
    result = Extraction(status="no_code", blocks_total=len(blocks), blocks_python=len(python_blocks))
    if not python_blocks:
        return result

    kept = []
    for body in python_blocks:
        try:
            tree = ast.parse(body)
        except SyntaxError:
            continue
        result.blocks_parsed += 1
        for node in tree.body:
            if isinstance(node, KEEP) or (isinstance(node, (ast.Assign, ast.AnnAssign)) and not _calls_something(node)):
                kept.append(node)
            else:
                kind = type(node).__name__
                result.dropped[kind] = result.dropped.get(kind, 0) + 1
    if result.blocks_parsed == 0:
        result.status = "unparseable"
        return result

    result.definitions_of_function = sum(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == function for n in kept)
    result.code = ast.unparse(ast.Module(body=kept, type_ignores=[])) + "\n"
    result.status = "ok" if result.definitions_of_function else "no_function"
    return result
