# Store long prompt strings here for clarity

def get_extraction_prompt(subject: str) -> str:
    return f"""
$
Silently analyze the text to:
a) Identify all nouns/noun phrases using syntactic tagging
b) Filter these to retain only concepts related to K-12 {subject}
c) STRICTLY OUTPUT ONLY the final K-12 {subject} concepts: In Simplified Chinese
As a single list using this exact format: -xxx\\n-xxx\\n-xxx
No headers/explanations/other text
Never reveal non-subject nouns or intermediate analysis.
$
"""

def get_feedback_prompt(subject: str) -> str:
    return f"""
$
---
Analyze the extracted K-12 {subject} concepts to:
a) NEVER modify or split original terms
b) Identify terms with cross-disciplinary ambiguity (e.g., terms that hold distinct meanings in other academic fields)
c) For each ambiguous term, provide a one-sentence clarification of its potential alternative academic meaning
d) Format output EXACTLY as: "ambiguous term" : "reason"
e) Output ONLY lines following this format without additional text
f) Preserve original lexical structure

Example analysis pattern:
"系统" : "Could refer to computer systems in technology contexts"

$
"""

def get_refine_prompt(subject: str, feedback: str, candidate_list_str: str) -> str:
    return f"""
$
Concept Filtering Protocol for K-12 {subject}

FEEDBACK ANALYSIS
$
{feedback}
$
(Note: Feedback analysis may contain errors.)
(Each feedback item clearly indicates terms that are out-of-scope or ambiguous with respect to K-12 {subject}.
For example, if feedback for "alcohol" indicates a chemistry context but not {subject}, then "alcohol" must be removed.)

CANDIDATE POOL
"{candidate_list_str}"

PROCESSING PIPELINE
1.Perform primary pruning using the FEEDBACK ANALYSIS to remove terms that are not directly relevant to K-12 {subject}.
2.Secondary filtration: Apply K-12 {subject} standards to ensure that all remaining terms are inherently {subject} concepts rather than instruments, apparatuses, or tools merely utilized in {subject} experiments.
(For example, although microscopes, objective lenses, temporary slides, and illumination components are used in {subject}, they are fundamentally tools from physics or engineering and should be removed.)
3. Eliminate redundancies and non-{subject} terms while preserving the original order.

OUTPUT SPECIFICATIONS
Strictly output in Markdown list format, with each term on a new line as follows:
- concept1
- concept2
- concept3
Maintain the original order of valid entries.
Output only the list, with no additional text.

Filtered Result:
$
"""