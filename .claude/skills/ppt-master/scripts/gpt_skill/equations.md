---
name: reduction-equations
description: Convert GHG reduction-project formulas and monitoring parameters into editable Office Math and tables in Word or PowerPoint, using KCS or Korean external-project forms. Use for supplied formulas, symbol definitions, monitoring plans, or importing equations from DOCX/PPTX.
---

# Editable reduction equations for ChatGPT and Work

Use native Office Math for formulas and parameter symbols. `${SKILL_DIR}` is
the folder containing this file. Read [`ENVIRONMENT.md`](./ENVIRONMENT.md), then
[`references/equation-workflow.md`](./references/equation-workflow.md).
All script paths in that workflow resolve against `${SKILL_DIR}/scripts`.

Preserve the user's source file and values. Import existing DOCX/PPTX equations
before rewriting them. Otherwise use their supplied formulas; never invent
coefficients, activity data, units or sources. Follow the supplied form, or
default to KCS when no form is specified. Confirm a current official form only
when submission accuracy requires it and browsing is available.

Use `monitoring_plan.py check` before export, resolve ERRORs, disclose WARNs,
and run `office_equations.py verify` on each output. Create only the requested
formats and use new versioned filenames. Equation structure and symbol/unit
mapping checks do not validate calculated emissions or coefficient accuracy.

This portable edition excludes the local web editor and Tailscale service.
For interactive corrections, show formulas and a parameter table in chat, apply
the user's changes to the plan file, and export a new version. For an editable
PPTX equation also verify that the package contains `a14:m` and `m:oMath`.
Render when a renderer exists; otherwise clearly report rendering unverified.

Return the requested files, equation/parameter counts, form, verification
results, remaining warnings and rendering status. Do not state that numerical
calculations were validated unless a separate calculation check was performed.
