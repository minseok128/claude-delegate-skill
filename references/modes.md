# Modes

Use exactly one mode per invocation.

## `review`

Use for a normal second opinion on the current diff, selected files, or a narrow design decision.

Include:

- task summary
- target files or diff
- relevant test failures

Expect:

- short summary
- concrete findings
- concrete risks
- recommended next steps

Defaults:

- schema: `scripts/schemas/review.json`
- settings: `scripts/settings/review.json`
- model: `opus`
- turns: `100`
- budget: `50`

## `adversarial-review`

Use for red-team style review. Ask Claude to challenge assumptions, identify breakage scenarios, and point out where the current reasoning is weak.

Include:

- the proposal or diff under test
- assumptions that seem fragile
- any compatibility or rollout constraints

Expect:

- summary of the most likely failure shape
- assumptions under test
- breakage scenarios
- disagreement points
- recommended next steps

Defaults:

- schema: `scripts/schemas/adversarial_review.json`
- settings: `scripts/settings/review.json`
- model: `opus`
- turns: `100`
- budget: `50`

## `implementation-plan`

Use when Codex should stay the executor but wants an alternative stepwise plan or tradeoff analysis before editing.

Include:

- current objective
- known constraints
- affected files or subsystems
- existing failed attempts, if any

Expect:

- concise plan summary
- ordered plan steps
- tradeoffs
- open questions
- confidence level

Defaults:

- schema: `scripts/schemas/implementation_plan.json`
- settings: `scripts/settings/plan.json`
- model: `opus`
- turns: `100`
- budget: `50`
