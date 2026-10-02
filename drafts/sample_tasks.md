# Sample tasks (DRAFT v0, for Clark to react to)

Five original beginner tasks, English only. I wrote them for this project; they are not
adapted from any textbook or course. Tagalog and Mandarin versions are left for you to
write, so I haven't machine-translated anything.

Each task has:

- **Spec**: the task itself, in a casual novice voice. It is identical across the two phrasings.
- **Two framings** wrapped around the spec (see "Framing templates" below).
- **Hidden spec tests** in `sample_tasks/test_*.py`. These are scored for RQ4 and only check
  behaviour the prompt states. All pass against `sample_tasks/reference/`.
- **Probes**. These are edge cases the prompt leaves open. They are **not scored**. The checker
  calls them and records what happens (return value or exception type), so we can compare the
  code's behaviour with the assumptions the response states (codebook code C2).

Every spec names the function, because the hidden tests have to call it. This is realistic:
novices often get a function name from an assignment. It does make the prompts a bit more
structured than a pure "vibe" request (see open question Q3).

---

## Framing templates (applied to every task)

The framing is a fixed wrapper, so the only thing that differs between conditions is the
framing (RQ2) or the language (RQ3). The task wording itself stays the same.

**MAKE** ("just make it"):
```
{spec}

can you just write it for me? i just need it to work.
```

**LEARN** ("help me learn"):
```
i'm learning python and i want to actually understand this, not just copy it.

{spec}

can you help me learn how to do it?
```

> Design note: MAKE doesn't say "code only, no explanation". If it did, we'd be measuring
> instruction-following rather than what the assistant volunteers. That's your call, though (Q2).

---

## T01 · split_bill (arithmetic, rounding)

**Spec (EN)**
```
i need a python function called split_bill(total, people, tip_percent). it should add the tip
to the total and then split it evenly, so it returns how much each person pays, rounded to 2
decimal places. for example split_bill(100, 4, 20) should give 30.0
```
**Probes:** `split_bill(50, 0, 10)` (zero people) · `split_bill("100", "4", "20")` (strings)

## T02 · longest_streak (loop with running state)

**Spec (EN)**
```
i'm tracking which days i practiced guitar as a list of True/False, one per day. write a python
function longest_streak(days) that returns the longest number of days in a row i practiced.
for example longest_streak([True, True, False, True, True, True, False]) should return 3
```
**Probes:** `longest_streak([])` · `longest_streak([1, 1, 0, 1])` (ints instead of bools)

## T03 · to_minutes (string parsing, 12-hour clock)

**Spec (EN)**
```
write a python function to_minutes(time_text) that takes a time like "7:05 PM" and returns how
many minutes have passed since midnight. so to_minutes("7:05 PM") should be 1145. the time is
always written like H:MM then a space then AM or PM. 12:00 AM is midnight and 12:00 PM is noon.
```
**Probes:** `to_minutes("7:05 pm")` (lowercase) · `to_minutes("07:05PM")` (no space) · `to_minutes("13:00 PM")`

## T04 · merge_lists (dictionaries, normalising keys)

**Spec (EN)**
```
me and my roommate each have a shopping list as a python dictionary of item name to quantity.
write a function merge_lists(list_a, list_b) that combines them into one dictionary. if the same
item is on both lists add the quantities together. item names should not care about upper or
lower case, and the result should use lowercase names. example:
merge_lists({"Eggs": 6, "milk": 1}, {"eggs": 12, "Bread": 2}) gives {"eggs": 18, "milk": 1, "bread": 2}
```
**Probes:** whether the inputs are mutated · `merge_lists({" eggs ": 1}, {"eggs": 1})` (whitespace)

## T05 · best_average (aggregation, tie-breaking)

**Spec (EN)**
```
i have a dictionary of student names to a list of their quiz scores. write a python function
best_average(scores) that returns the name of the student with the highest average score. if two
students tie, return the name that comes first alphabetically.
for example best_average({"Ana": [80, 90], "Ben": [100, 60, 95], "Chen": [70]}) should return "Ana"
```
**Probes:** `best_average({})` · `best_average({"Ana": [], "Ben": [50]})` (empty score list)

---

## Notes on the set

- Difficulty runs from one-liner (T01) to tie-breaking logic (T05). For the full 20, I'd aim
  for roughly 6 easy, 8 medium, and 6 slightly tricky tasks, covering the same concepts as an
  intro course (conditionals, loops, strings, lists, dicts, functions).
- The contexts (splitting a bill, guitar practice, shopping, quizzes) are meant to be culturally
  neutral, so they read naturally in all three languages. If you'd rather localise names or
  items per language, decide that now: it adds realism but also a second difference between
  conditions.
- **Code identifiers stay in English in every language.** Function names, `True`/`False`, and
  the example calls are identical everywhere, and only the prose is translated. This is also how
  multilingual novices actually write.
