"""
Candidate replacement instructions for `sentence_moderate_controlled_v2`
(review item 4, 2026-08-13) -- DESIGN ONLY, NOT YET TESTED.

EXP-DATA-001-R2's controlled comparison (context and temperature held
constant between light/moderate) isolated instruction wording/
transformation strength as the most plausible remaining cause of
`sentence_moderate_controlled_v2`'s 33% semantic-drift rate (see DEC-011
"Category-Specific Conclusions"). The existing instruction asks the model
to "preserve its meaning" in the abstract, without saying what that
means -- these candidates replace that vague instruction with an
explicit, itemized preservation checklist (mirroring the drift/non-drift
categories already documented in generation-methodology.md Section 12),
while still explicitly permitting MORE stylistic restructuring than the
light instruction allows. That's the actual design goal: stronger
restructuring latitude, zero factual/claim latitude.

Per explicit instruction: do NOT run a large-scale (or any) generation
experiment with these yet, and do NOT choose a "winner" based on
pass-rate against existing samples -- that would be exactly the kind of
threshold-shopping this project's discipline forbids. A future,
explicitly authorized experiment should test these against fresh seeds,
with the SAME controls already established (model, revision, temperature
0.6/top_p 0.95, full-paragraph context, span-selection, QC, and the
DEC-012 screen) -- varying ONLY the instruction wording, per the
experimental-independence principle (review item 6).
"""

# --- Candidate M1: explicit preservation checklist ---
# Directly enumerates what must NOT change, using the same vocabulary as
# generation-methodology.md Section 12's drift protocol (numbers,
# entities, actor/action, causal relationships, position/conclusion).
# Rationale: the current instruction's only preservation language is
# "preserving its meaning" -- vague enough that a model satisfying
# "reword for clarity and flow" can plausibly believe it has complied
# while still substituting a claim or a number. An itemized checklist
# gives the model concrete, checkable constraints instead of one vague
# one.
CANDIDATE_M1_INSTRUCTION = (
    "You are editing ONE sentence within a paragraph. Reword the SPECIFIC TARGET SENTENCE below "
    "for clarity, flow, and stronger phrasing -- you may restructure it more freely than a light "
    "copy-edit (change sentence structure, combine or reorder clauses, choose different words), "
    "but the reworded sentence MUST keep, unchanged: every number and quantity, every named "
    "person/place/organization, who performs each action and to whom, every cause-and-effect "
    "relationship stated, and the author's stated position or conclusion. Do NOT introduce a new "
    "claim, drop a claim, change a number, change who did what, or soften/reverse the author's "
    "stated position. Do NOT change, paraphrase, or rewrite any other sentence in the paragraph. "
    "Return ONLY the reworded target sentence, with no preamble, quotation marks, or commentary.\n\n"
    "Full paragraph for context:\n{paragraph}\n\nTarget sentence to edit: {target}"
)
CANDIDATE_M1_META = (
    "You are editing ONE sentence within a paragraph. Reword the SPECIFIC TARGET SENTENCE below "
    "for clarity, flow, and stronger phrasing -- you may restructure it more freely than a light "
    "copy-edit (change sentence structure, combine or reorder clauses, choose different words), "
    "but the reworded sentence MUST keep, unchanged: every number and quantity, every named "
    "person/place/organization, who performs each action and to whom, every cause-and-effect "
    "relationship stated, and the author's stated position or conclusion. Do NOT introduce a new "
    "claim, drop a claim, change a number, change who did what, or soften/reverse the author's "
    "stated position. Do NOT change, paraphrase, or rewrite any other sentence in the paragraph. "
    "Return ONLY the reworded target sentence, with no preamble, quotation marks, or commentary."
)

# --- Candidate M2: checklist + silent self-check step ---
# Same preservation checklist as M1, plus an explicit instruction to
# silently verify the constraint before answering. Still returns only
# the final sentence (no visible chain-of-thought/commentary allowed --
# that would itself risk instruction-leakage-style contamination of the
# sample text). Rationale: instruction-following literature and this
# project's own observation (moderate produces MORE drift than light
# despite both receiving a "preserve meaning" instruction) suggest an
# explicit verify-before-answering step may help small instruction-tuned
# models comply with constraints they'd otherwise silently drop under
# competing pressure to "reword for clarity."
CANDIDATE_M2_INSTRUCTION = (
    CANDIDATE_M1_INSTRUCTION.replace(
        "Return ONLY the reworded target sentence",
        "Before answering, silently check: does your reworded sentence contain the exact same "
        "facts, numbers, names, and conclusion as the original target sentence? If not, revise it "
        "until it does. Return ONLY the reworded target sentence",
    )
)
CANDIDATE_M2_META = (
    CANDIDATE_M1_META.replace(
        "Return ONLY the reworded target sentence",
        "Before answering, silently check: does your reworded sentence contain the exact same "
        "facts, numbers, names, and conclusion as the original target sentence? If not, revise it "
        "until it does. Return ONLY the reworded target sentence",
    )
)

# --- Candidate M3: checklist + concrete negative example ---
# Same preservation checklist as M1, plus a concrete, generic example of
# the actual failure mode observed in this project's real data (the
# "one C" -> "two Cs" case from EXP-DATA-001-R1-confirmation, and the
# "specific grievance replaced by a generic sentence" case) -- grounding
# the abstract constraint in the specific kind of mistake this model has
# actually made, rather than trusting the model to infer what "changing
# a claim" means from the checklist alone.
CANDIDATE_M3_INSTRUCTION = (
    CANDIDATE_M1_INSTRUCTION.replace(
        "Return ONLY the reworded target sentence",
        "For example: if the original says 'at least one', do not write 'at least two'; if the "
        "original gives a specific reason, do not replace it with a different or more generic "
        "reason. Return ONLY the reworded target sentence",
    )
)
CANDIDATE_M3_META = (
    CANDIDATE_M1_META.replace(
        "Return ONLY the reworded target sentence",
        "For example: if the original says 'at least one', do not write 'at least two'; if the "
        "original gives a specific reason, do not replace it with a different or more generic "
        "reason. Return ONLY the reworded target sentence",
    )
)

CANDIDATES = {
    "M1_explicit_checklist": (CANDIDATE_M1_INSTRUCTION, CANDIDATE_M1_META),
    "M2_checklist_plus_selfcheck": (CANDIDATE_M2_INSTRUCTION, CANDIDATE_M2_META),
    "M3_checklist_plus_negative_example": (CANDIDATE_M3_INSTRUCTION, CANDIDATE_M3_META),
}
