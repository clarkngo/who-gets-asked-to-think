"""Text normalisation shared by the prompt builder and the translation checker."""
import re

CJK = re.compile(r"[一-鿿]")


def flatten(text):
    """Join wrapped lines within a paragraph, the way a person would type them.

    The YAML prompt files wrap long lines for readability. Before a prompt is sent, lines inside
    a paragraph are joined with a space (or with nothing when either side is a CJK character).
    Blank lines (paragraph breaks) are kept.
    """
    paragraphs = re.split(r"\n\s*\n", (text or "").strip())
    out = []
    for para in paragraphs:
        lines = [line.strip() for line in para.split("\n") if line.strip()]
        joined = lines[0] if lines else ""
        for line in lines[1:]:
            sep = "" if CJK.match(joined[-1]) or CJK.match(line[0]) else " "
            joined += sep + line
        out.append(joined)
    return "\n\n".join(out)
