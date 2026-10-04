"""Pull the solution code out of a model response.

Rule (applied identically to every response):
1. Take every fenced code block tagged python/py, or untagged. Blocks tagged as another language
   (bash, text, output, ...) are ignored.
2. Parse each block on its own and skip any that aren't valid Python (e.g. REPL transcripts
   with >>> prompts, or snippets with "...").
3. Concatenate the valid blocks in order and keep only top-level imports, function and class
   definitions, and assignments that call nothing AND use only names already defined (or
   builtins), i.e. real constants. Demo code such as print(split_bill(100, 4, 20)), input(),
   loops, `if __name__ == "__main__":` blocks, and teaching fragments like `period = parts[1]`
   are dropped, so the tests judge the function rather than the text around it.
4. If the required function is defined more than once, definitions that never return a value
   are skipped (e.g. an "add this line" snippet ending in "# ... rest stays the same"), since
   every task requires returning a value. Of the rest, the last definition wins.
5. `has_placeholder` flags a chosen function that still contains `pass`, `...` or
   NotImplementedError: likely deliberate scaffolding. It is recorded, not used for the status.

Version history: v1 kept any call-free assignment and always used the last definition;
v2 (Oct 3, 2026) added the defined-names check, the no-return skip, and has_placeholder.

Statuses: ok | no_code (no Python blocks) | unparseable (blocks, none valid) |
          no_function (valid code, but the required function isn't defined at top level)
"""
import ast
import builtins
import re
from dataclasses import dataclass, field

FENCE = re.compile(r"```[ \t]*([A-Za-z0-9_+-]*)[^\n]*\n(.*?)```", re.S)
PYTHON_TAGS = {"", "python", "py", "python3"}
DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
BUILTINS = set(dir(builtins))


@dataclass
class Extraction:
    status: str
    code: str = ""
    blocks_total: int = 0           # all fenced blocks
    blocks_python: int = 0          # python/untagged blocks
    blocks_parsed: int = 0          # python blocks that parsed
    definitions_of_function: int = 0
    definitions_skipped_no_return: int = 0
    has_placeholder: bool = False
    dropped: dict = field(default_factory=dict)  # statement kind -> count


def _calls_something(node) -> bool:
    return any(isinstance(n, ast.Call) for n in ast.walk(node))


def extract(response: str, function: str) -> Extraction:
    blocks = FENCE.findall(response or "")
    python_blocks = [body for tag, body in blocks if tag.lower() in PYTHON_TAGS]
    result = Extraction(status="no_code", blocks_total=len(blocks), blocks_python=len(python_blocks))
    if not python_blocks:
        return result

    kept, defined = [], set()

    def drop(kind):
        result.dropped[kind] = result.dropped.get(kind, 0) + 1

    for body in python_blocks:
        try:
            tree = ast.parse(body)
        except SyntaxError:
            continue
        result.blocks_parsed += 1
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                kept.append(node)
                defined.update((a.asname or a.name).split(".")[0] for a in node.names)
            elif isinstance(node, DEFS):
                kept.append(node)
                defined.add(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                if value is None or _calls_something(node):
                    drop("Assign")
                    continue
                used = {n.id for n in ast.walk(value) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if used - defined - BUILTINS or not all(isinstance(t, ast.Name) for t in targets):
                    drop("Assign (undefined name)")
                    continue
                kept.append(node)
                defined.update(t.id for t in targets)
            else:
                drop(type(node).__name__)
    if result.blocks_parsed == 0:
        result.status = "unparseable"
        return result

    is_target = lambda n: isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == function
    targets = [n for n in kept if is_target(n)]
    result.definitions_of_function = len(targets)
    returning = [n for n in targets if _returns_value(n)]
    if returning and len(returning) < len(targets):
        skip = {id(n) for n in targets if n not in returning}
        result.definitions_skipped_no_return = len(skip)
        kept = [n for n in kept if id(n) not in skip]
        targets = returning
    if targets:
        result.has_placeholder = _has_placeholder(targets[-1])
    result.code = ast.unparse(ast.Module(body=kept, type_ignores=[])) + "\n"
    result.status = "ok" if targets else "no_function"
    return result


def _returns_value(fn) -> bool:
    return any((isinstance(n, ast.Return) and n.value is not None) or isinstance(n, (ast.Yield, ast.YieldFrom))
               for n in ast.walk(fn))


def _has_placeholder(fn) -> bool:
    for n in ast.walk(fn):
        if isinstance(n, ast.Pass):
            return True
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and n.value.value is Ellipsis:
            return True
        if isinstance(n, ast.Raise) and "NotImplementedError" in ast.unparse(n):
            return True
    return False
