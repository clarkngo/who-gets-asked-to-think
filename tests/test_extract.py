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
