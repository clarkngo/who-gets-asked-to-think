# Task set (DRAFT v1: all 20 tasks, English)

> The prompt text used by the pipeline lives in `prompts/en.yaml`, which is canonical. This file is
> the human-readable overview, with probes and design notes.

Twenty original beginner tasks, English only. I wrote them for this project; they are not
adapted from any textbook or course. Clark approved T01–T05 on Oct 2, and T06–T20 are new drafts in
the same style. Tagalog and Mandarin versions are left for you to
write, so I haven't machine-translated anything.

Each task has:

- **Spec**: the task itself, in a casual novice voice. It is identical across the two phrasings.
- **Two framings** wrapped around the spec (see "Framing templates" below).
- **Hidden spec tests** in `sample_tasks/test_*.py` (kept private and gitignored until the pilot run is done). These are scored for RQ4 and only check
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

## T01 · split_bill (arithmetic, rounding) · easy

**Spec (EN)**
```
i need a python function called split_bill(total, people, tip_percent). it should add the tip
to the total and then split it evenly, so it returns how much each person pays, rounded to 2
decimal places. for example split_bill(100, 4, 20) should give 30.0
```
**Probes:** `split_bill(50, 0, 10)` (zero people) · `split_bill("100", "4", "20")` (strings)

## T02 · longest_streak (loop with running state) · medium

**Spec (EN)**
```
i'm tracking which days i practiced guitar as a list of True/False, one per day. write a python
function longest_streak(days) that returns the longest number of days in a row i practiced.
for example longest_streak([True, True, False, True, True, True, False]) should return 3
```
**Probes:** `longest_streak([])` · `longest_streak([1, 1, 0, 1])` (ints instead of bools)

## T03 · to_minutes (string parsing, 12-hour clock) · medium

**Spec (EN)**
```
write a python function to_minutes(time_text) that takes a time like "7:05 PM" and returns how
many minutes have passed since midnight. so to_minutes("7:05 PM") should be 1145. the time is
always written like H:MM then a space then AM or PM. 12:00 AM is midnight and 12:00 PM is noon.
```
**Probes:** `to_minutes("7:05 pm")` (lowercase) · `to_minutes("07:05PM")` (no space) · `to_minutes("13:00 PM")`

## T04 · merge_lists (dictionaries, normalising keys) · medium

**Spec (EN)**
```
me and my roommate each have a shopping list as a python dictionary of item name to quantity.
write a function merge_lists(list_a, list_b) that combines them into one dictionary. if the same
item is on both lists add the quantities together. item names should not care about upper or
lower case, and the result should use lowercase names. example:
merge_lists({"Eggs": 6, "milk": 1}, {"eggs": 12, "Bread": 2}) gives {"eggs": 18, "milk": 1, "bread": 2}
```
**Probes:** whether the inputs are mutated · `merge_lists({" eggs ": 1}, {"eggs": 1})` (whitespace) · `merge_lists({"Tea": 1, "TEA": 2}, {})` (two spellings in one list; moved from the scored tests on Oct 3)

## T05 · best_average (aggregation, tie-breaking) · harder

**Spec (EN)**
```
i have a dictionary of student names to a list of their quiz scores. write a python function
best_average(scores) that returns the name of the student with the highest average score. if two
students tie, return the name that comes first alphabetically.
for example best_average({"Ana": [80, 90], "Ben": [100, 60, 95], "Chen": [70]}) should return "Ana"
```
**Probes:** `best_average({})` · `best_average({"Ana": [], "Ben": [50]})` (empty score list)

## T06 · temperature_label (if/elif boundaries) · easy

**Spec (EN)**
```
write a python function temperature_label(celsius) that gives a word for the weather. below 10
is "cold", 25 or above is "hot", and anything in between is "mild". for example
temperature_label(30) should return "hot"
```
**Probes:** `temperature_label("20")` (string) · `temperature_label(None)`

## T07 · count_long_words (split + counting) · easy

**Spec (EN)**
```
write a python function count_long_words(sentence, min_length) that counts how many words in the
sentence have at least min_length letters. the words are separated by single spaces. for example
count_long_words("i love writing small programs", 5) should return 3
```
**Probes:** `count_long_words("hello, world!", 6)` (punctuation counted as letters?) · double spaces · `count_long_words("", 1)`

## T08 · initials (string building) · easy

**Spec (EN)**
```
write a python function initials(full_name) that takes a name with the words separated by single
spaces and returns the first letter of each word in uppercase, each followed by a dot. for example
initials("maria clara santos") should return "M.C.S."
```
**Probes:** `initials("  ana  cruz ")` (extra spaces) · `initials("")` · `initials("jean-luc picard")`

## T09 · days_met_goal (loop + condition) · easy

**Spec (EN)**
```
i have a list of how many steps i walked each day. write a python function
days_met_goal(steps, goal) that returns how many days i walked at least goal steps. for example
days_met_goal([8000, 12000, 10000, 4000], 10000) should return 2
```
**Probes:** `days_met_goal([], 5000)` · `days_met_goal([100, -50], 0)` (negative steps)

## T10 · price_after_coupon (conditionals on strings) · easy

**Spec (EN)**
```
write a python function price_after_coupon(price, coupon). if the coupon is "HALF" the price is
cut in half. if the coupon is "TENOFF" take 10 off the price, but the price can never go below 0.
any other coupon does nothing and you just get the normal price. for example
price_after_coupon(30, "TENOFF") should return 20
```
**Probes:** `price_after_coupon(30, "half")` (lowercase) · `price_after_coupon(30, " HALF ")` · `price_after_coupon(-5, "HALF")`

## T11 · group_by_first_letter (dict of lists) · medium

**Spec (EN)**
```
write a python function group_by_first_letter(names) that takes a list of names and returns a
dictionary. the keys are the first letter of the names in uppercase, and each value is the list of
names that start with that letter, in the same order they were in the original list. keep the
names spelled exactly as they were. for example
group_by_first_letter(["ana", "Ben", "alex", "bea"]) should return {"A": ["ana", "alex"], "B": ["Ben", "bea"]}
```
**Probes:** `group_by_first_letter([])` · `group_by_first_letter([""])` (empty name)

## T12 · running_total (accumulator) · medium

**Spec (EN)**
```
i'm tracking what i spend. write a python function running_total(expenses) that takes a list of
amounts and returns a new list where each number is the total spent so far. for example
running_total([5, 3, 10]) should return [5, 8, 18]
```
**Probes:** `running_total([])` · `running_total([0.1, 0.2])` (float display) · whether the input list is mutated

## T13 · censor (word-level replace, case-insensitive) · medium

**Spec (EN)**
```
write a python function censor(text, banned) where text is a sentence with words separated by
single spaces and banned is a list of words. replace every word that is banned with stars, using
the same number of stars as the word has letters. upper or lower case shouldn't matter when
checking. all the other words stay exactly the same. for example
censor("this is so Darn annoying", ["darn"]) should return "this is so **** annoying"
```
**Probes:** `censor("oh darn!", ["darn"])` (punctuation attached) · `censor("darnit", ["darn"])` (banned word inside another word) · `censor("ok", [])`

## T14 · seats_left (state + skip rule) · medium

**Spec (EN)**
```
write a python function seats_left(capacity, bookings) for a small bus. bookings is a list of
numbers. a positive number means that many seats get booked. a negative number means that many
seats got cancelled. if a booking asks for more seats than are left, skip that booking completely.
return how many seats are left at the end. for example seats_left(10, [4, 5, 3, -2]) should return 3
```
**Probes:** `seats_left(10, [-3])` (cancel more than booked) · `seats_left(0, [1])` · `seats_left(5, [0])`

## T15 · parse_scores (string parsing → dict) · medium

**Spec (EN)**
```
i have quiz scores saved as text like "Ana:90,Ben:75,Chen:88". write a python function
parse_scores(text) that turns it into a dictionary of name to score, where the score is an int.
for example parse_scores("Ana:90,Ben:75,Chen:88") should return {"Ana": 90, "Ben": 75, "Chen": 88}
```
**Probes:** `parse_scores("Ana: 90, Ben:75")` (spaces) · `parse_scores("Ana:90,Ana:80")` (duplicate name) · `parse_scores("")` · `parse_scores("Ana:90,")` (trailing comma)

## T16 · minutes_until_next_bus (time arithmetic, wrap-around) · harder

**Spec (EN)**
```
write a python function minutes_until_next_bus(schedule, now). schedule is a list of bus times
like ["06:30", "12:15", "18:45"] in 24 hour time, already sorted. now is the current time in the
same format. return how many minutes until the next bus. if a bus leaves exactly now, that counts
and the answer is 0. if there are no more buses today, return the minutes until the first bus
tomorrow. for example minutes_until_next_bus(["06:30", "12:15", "18:45"], "12:00") should return 15
```
**Probes:** unsorted schedule · `minutes_until_next_bus([], "12:00")` · `"6:30"` without the leading zero

## T17 · make_teams (slicing + special case) · harder

**Spec (EN)**
```
write a python function make_teams(names, team_size) that splits a list of names into teams of
team_size, keeping the original order. the last team is allowed to be smaller, but if the last
team would only have 1 person, put that person into the team before it instead. return a list of
teams, where each team is a list of names. for example
make_teams(["a", "b", "c", "d", "e", "f", "g"], 3) should return [["a", "b", "c"], ["d", "e", "f", "g"]]
```
**Probes:** `make_teams(["a"], 3)` (only one team, of 1) · `make_teams(["a", "b", "c"], 1)` (rule conflicts with team_size 1) · `make_teams([], 3)`

## T18 · format_duration (divmod + formatting) · harder

**Spec (EN)**
```
write a python function format_duration(seconds) that takes a whole number of seconds and returns
it like "1h 5m 3s". leave out any part that is zero, so 3600 is just "1h" and 3601 is "1h 1s".
don't use days, so hours can go above 24. if seconds is 0 return "0s". for example
format_duration(3903) should return "1h 5m 3s"
```
**Probes:** `format_duration(-5)` · `format_duration(61.5)` (float)

## T19 · make_usernames (dict counting, dedup) · harder

**Spec (EN)**
```
write a python function make_usernames(full_names). for each name, make a username by turning it
lowercase and removing the spaces. if that username was already used by an earlier name in the
list, add 2 to the end, then 3 for the next one, and so on. return the list of usernames in the
same order. for example make_usernames(["Ana Cruz", "ana cruz", "Ben Lee", "ANA CRUZ"]) should
return ["anacruz", "anacruz2", "benlee", "anacruz3"]
```
**Probes:** `make_usernames(["Ana Cruz2", "Ana Cruz", "Ana Cruz"])` (generated name collides with a real one) · `make_usernames([""])` · `make_usernames(["José Rizal"])` (accents)

## T20 · reading_plan (integer division + remainder) · harder

**Spec (EN)**
```
i want to finish a book over some number of days. write a python function
reading_plan(total_pages, days) that returns a list with how many pages to read each day. split the
pages as evenly as possible, and if they don't divide evenly the earlier days get one extra page.
for example reading_plan(10, 3) should return [4, 3, 3]
```
**Probes:** `reading_plan(10, 0)` · `reading_plan(-3, 2)`

---

## Notes on the set

| Difficulty | Tasks | Concepts covered |
|---|---|---|
| Easy (6) | T01, T06, T07, T08, T09, T10 | arithmetic, if/elif, string split, string building, counting loops |
| Medium (8) | T02, T03, T04, T11, T12, T13, T14, T15 | running state, parsing, dict building, dicts of lists, accumulators, case handling |
| Harder (6) | T05, T16, T17, T18, T19, T20 | tie-breaking, wrap-around time, special-case rules, divmod formatting, dedup counters, remainders |

- **Hidden tests check only what the prompt states.** Anything the prompt leaves open is a probe.
  It's recorded but never scored.
- The contexts (bills, guitar practice, shopping, quizzes, steps, buses, books) are meant to be
  culturally neutral, so they read naturally in all three languages. When you translate, keep the
  example names (Ana, Ben, Chen, Li Wei, Tala…) unchanged. They already mix Filipino, Chinese and
  English names, and keeping them the same means names never differ between language conditions.
- **Code identifiers stay in English in every language.** Function names, `True`/`False`, and
  the example calls are identical everywhere, and only the prose is translated. This is also how
  multilingual novices actually write.
- **For translators (Clark):** please keep every number, string literal and example call
  character-for-character identical. Only the surrounding prose changes.
