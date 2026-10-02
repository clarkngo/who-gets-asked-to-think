# ThinkCheck codebook (DRAFT v0, first pass for Clark to refine)

**Unit of analysis:** one complete model response to one prompt.
**Coding scheme:** each code is binary (present = 1 / absent = 0). Binary codes keep the
agreement statistics (Cohen's κ) simple and are easier to apply consistently as a single coder.
We can add a 0/1/2 depth scale for C1 later if the binary version turns out too coarse.
**What counts:** the prose and any comments inside code blocks, but only where a comment does
more than restate the line. See the decision rules below.
**Language:** code the response in whatever language it is written in. Clark codes all three
languages, so no translation step is needed.

Codes C1–C5 map onto the evaluative-judgment features in RQ1. C6 captures a different kind of
"asking the learner to think" (withholding the answer). Section B lists features that the
pipeline measures automatically, so nobody hand-codes them.

---

## A. Hand-coded features

### C1 · EXPLAINS_MECHANISM
**Definition.** The response explains *how or why* the code works: the logic, the order of
steps, or why a particular construct was chosen. A description of *what* the code does
doesn't count.
**Example.** "We reset `current` to 0 whenever a day is False, because a streak has to be
unbroken. `best` keeps the largest value we've seen so far."
**Non-example.** "This function returns the longest streak." (It restates the task.)
"Here's the code:" followed only by code.
**Decision rule.** A single substantive sentence of mechanism is enough. Inline comments count
only if they give a reason (`# % 12 turns 12 AM into 0`), not a label (`# loop through days`).

### C2 · STATES_ASSUMPTIONS_OR_LIMITS
**Definition.** The response says what conditions the code depends on, what inputs it does not
handle, or what it would do on edge cases.
**Example.** "This assumes `people` is at least 1. If it's 0 you'll get a ZeroDivisionError."
"Note: this only works if the time always has a space before AM/PM."
**Non-example.** Code that silently handles an edge case (`if not days: return 0`) without
mentioning it in prose or a comment. (That is behaviour, and the probes capture it.)
**Decision rule.** The response has to name the assumption or limit; handling it in code isn't
enough. Restating a constraint the prompt already gave ("rounded to 2 decimals") doesn't count.

### C3 · FLAGS_UNCERTAINTY
**Definition.** The response signals that it might be wrong or incomplete, or that its
correctness hasn't been confirmed: it hedges about its *own output*.
**Example.** "I haven't run this, so double-check the rounding." "Floating-point rounding can
sometimes give 49.16 vs 49.17, so you may want to test that case."
**Non-example.** A confident statement of a limitation ("this doesn't handle 0 people"). That
is C2. Generic politeness ("hope this helps!").
**Decision rule.** C2 is about the problem: "this input breaks it". C3 is about the answer's
reliability: "I might be wrong about X". One sentence can be both, and then both are coded.

### C4 · SUGGESTS_VERIFICATION
**Definition.** The response gives the learner a concrete way to check the code: specific test
inputs to try, `assert`s or test cases, "print X to see Y", or comparing against a hand
calculation.
**Example.** "Try `longest_streak([])` and `longest_streak([False])`. Both should give 0."
A `print(split_bill(100, 4, 20))  # should print 30.0` that is presented for the learner to run.
**Non-example.** A bare usage example the model presents as the answer ("Output: 3") with no
invitation to check. "Make sure to test your code." (Too vague: there's no concrete method.)
**Decision rule.** It has to be concrete (a specific input, assertion, or procedure) *and*
framed as something the learner does or checks.

### C5 · INVITES_PREDICTION_OR_MODIFICATION
**Definition.** The response asks the learner to predict behaviour, explain something back,
change or extend the code, or answer a question before going on.
**Example.** "What do you think happens if every day is False? Try predicting before you run
it." "Challenge: change it so it also returns *which* days the streak started."
**Non-example.** "Let me know if you have questions!" (A generic offer, not an invitation to
think.)
**Decision rule.** The invitation has to name a specific thing to predict, explain, or modify.

### C6 · SCAFFOLDS_INSTEAD_OF_SOLVING
**Definition.** The response deliberately leaves out a complete working solution. It gives
hints, pseudocode, partial code, or step-by-step guidance and leaves the learner to finish.
**Example.** "Here's the outline. Try filling in the part that updates `best`:" followed by
code with a `# TODO`.
**Non-example.** A complete solution followed by an explanation. That is C1, not C6.
**Decision rule.** Code C6 only if the response contains **no** runnable, complete solution
to the task. The pipeline also flags "no complete solution found" automatically (B3). C6 is the
human confirmation that the withholding was deliberate rather than a failure.

---

## B. Automatically measured (not hand-coded)

| ID | Feature | How |
|---|---|---|
| B1 | Response language | Language-ID on the prose with code blocks removed. Does it match the prompt language? Clark spot-checks. |
| B2 | Prose : code ratio | Characters outside code blocks vs inside. |
| B3 | Complete solution present | Was a code block extracted that defines the required function? |
| B4 | Spec tests passed | Sandbox result (RQ4): pass / fail / error / timeout / no-code. |
| B5 | Probe behaviour | Return value or exception type per probe. |
| B6 | Length | Total tokens/characters of the visible response. |

**Composite (descriptive only).** An *evaluative-judgment count* = C1+C2+C3+C4+C5 (0–5). This
is a convenience summary and not a validated scale, and the write-up will say so.

---

## Open coding questions for Clark

1. Should C1 have depth levels (0 = none, 1 = names the steps, 2 = explains why)?
2. A response that answers in English to a Tagalog prompt: should that be coded as anything
   beyond B1? (It is arguably the most RQ3-relevant finding.)
3. Do you want a code for **deference/agency language** ("you might choose to…", "it's up to
   you whether…") versus directive language? It fits your "not outsourcing the thinking" agenda,
   but it is harder to code reliably.
4. Code-switching (Taglish, or Mandarin prose with English terms) is normal and should *not*
   count as a language mismatch. Agree?
