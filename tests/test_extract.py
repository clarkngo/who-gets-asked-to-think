from thinkcheck.extract import extract

FN = "split_bill"


def test_takes_python_block_and_drops_demo_code():
    resp = "Here:\n```python\ndef split_bill(t, p, tip):\n    return round(t*(1+tip/100)/p, 2)\n\nprint(split_bill(100, 4, 20))\nx = input()\n```\nDone."
    ex = extract(resp, FN)
    assert ex.status == "ok"
    assert "print" not in ex.code and "input" not in ex.code
    assert ex.dropped == {"Expr": 1, "Assign": 1}


def test_untagged_block_counts_other_languages_do_not():
    assert extract("```\ndef split_bill(a, b, c):\n    return 1\n```", FN).status == "ok"
    assert extract("```bash\npip install x\n```", FN).status == "no_code"


def test_no_code_and_unparseable_and_missing_function():
    assert extract("Just divide by the number of people.", FN).status == "no_code"
    assert extract("```python\n>>> split_bill(1, 2, 3)\n30.0\n```", FN).status == "unparseable"
    assert extract("```python\ndef helper():\n    pass\n```", FN).status == "no_function"


def test_last_definition_wins_and_helpers_from_earlier_blocks_are_kept():
    resp = ("```python\nRATE = 100\ndef split_bill(a, b, c):\n    return 0\n```\nBetter:\n"
            "```python\ndef split_bill(a, b, c):\n    return a / RATE\n```")
    ex = extract(resp, FN)
    assert ex.status == "ok" and ex.definitions_of_function == 2
    ns = {}
    exec(ex.code, ns)
    assert ns["split_bill"](200, 0, 0) == 2


def test_main_guard_and_calling_assignments_are_dropped():
    resp = ("```python\nimport math\nTIPS = [10, 15]\nresult = split_bill(1, 1, 1)\n"
            "def split_bill(a, b, c):\n    return math.floor(a)\n"
            "if __name__ == '__main__':\n    print(split_bill(1, 1, 1))\n```")
    ex = extract(resp, FN)
    assert "TIPS" in ex.code and "result" not in ex.code and "__main__" not in ex.code
    assert ex.dropped == {"Assign": 1, "If": 1}


def test_teaching_fragments_using_undefined_names_are_dropped():
    resp = ("First split it:\n```python\nparts = time_text.split()\nperiod = parts[1]\n```\n"
            "Full version:\n```python\nLIMIT = 10\nDOUBLE = LIMIT * 2\ndef split_bill(a, b, c):\n    return a + DOUBLE\n```")
    ex = extract(resp, FN)
    assert ex.dropped == {"Assign": 1, "Assign (undefined name)": 1}
    ns = {}
    exec(ex.code, ns)  # must not raise NameError
    assert ns["split_bill"](1, 0, 0) == 21


def test_partial_redefinition_without_return_is_skipped():
    resp = ("```python\ndef split_bill(a, b, c):\n    return a * 2\n```\nTo be safe add:\n"
            "```python\ndef split_bill(a, b, c):\n    a = float(a)  # ... rest stays the same\n```")
    ex = extract(resp, FN)
    assert ex.definitions_of_function == 2 and ex.definitions_skipped_no_return == 1
    ns = {}
    exec(ex.code, ns)
    assert ns["split_bill"](3, 0, 0) == 6


def test_scaffold_with_placeholders_is_flagged_not_rejected():
    resp = "```python\ndef split_bill(a, b, c):\n    total = 0\n    # TODO: add the tip\n    pass\n    return total\n```"
    ex = extract(resp, FN)
    assert ex.status == "ok" and ex.has_placeholder


def test_missing_opening_fence_is_repaired():
    resp = ("def split_bill(a, b, c):\n    return a\n```\n\nExamples:\n\n"
            "```python\nsplit_bill(1, 2, 3)  # 1\n```\n")
    ex = extract(resp, FN)
    assert ex.fence_repaired and ex.status == "ok"


def test_balanced_fences_are_not_repaired():
    ex = extract("Here:\n```python\ndef split_bill(a, b, c):\n    return a\n```", FN)
    assert not ex.fence_repaired


def test_ellipsis_anywhere_counts_as_placeholder():
    ex = extract("```python\ndef split_bill(a, b, c):\n    tip = ...\n    return ...\n```", FN)
    assert ex.status == "ok" and ex.has_placeholder


def test_fill_in_blank_counts_as_placeholder():
    ex = extract("```python\ndef split_bill(a, b, c):\n    if ______:\n        return 1\n    return 0\n```", FN)
    assert ex.has_placeholder
