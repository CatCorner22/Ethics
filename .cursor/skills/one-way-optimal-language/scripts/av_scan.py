"""Fallback active-voice regex scan for one-way-optimal-language (stdlib only)."""
import re
import sys

from _path_safe import PathValidationError, assert_input_size, validate_user_path

P = (
    r"(?:\w{2,}ed|cut|put|set|read|hit|shut|hurt|spread|cast|shed|upset|run|overcome|done|given|taken|"
    r"mistaken|shaken|made|seen|written|known|shown|grown|thrown|blown|drawn|withdrawn|sworn|torn|worn|"
    r"born|found|told|held|withheld|kept|left|built|brought|bought|caught|taught|thought|sought|sent|"
    r"spent|meant|dealt|felt|led|misled|fed|bred|lit|met|paid|laid|said|sold|driven|hidden|broken|"
    r"chosen|frozen|spoken|stolen|forgotten|begun|struck|stuck|understood|beaten|bitten|eaten|forbidden|"
    r"ridden|proven|swollen|bound|lost|shot|heard|dug|hung|won)"
)
NOT = r"(?!(?:need|bed|red|seed|feed|speed|bleed|breed|proceed|exceed|succeed|hundred|sacred|naked|wicked)\b)"
ADV = r"(?:\s+(?:\w+ly|not|n't|also|only|then|often|usually|always|never|already|still|just|all|last|first|now|again|been|being|be))*"
DET = r"(?:the|a|an|your|my|his|her|its|our|their|this|that|these|those|each|every|any)"
PATTERNS = [
    (
        "be/get/stay + participle",
        rf"\b(?:am|is|are|was|were|be|been|being|'s|'re|isn't|aren't|wasn't|weren't|get|gets|got|gotten|getting|remains?|remained|stays?|stayed|seems?|seemed|looks?|looked|feels?|felt|appears?|appeared|becomes?|became){ADV}\s+{NOT}{P}\b",
    ),
    (
        "question: be ... participle",
        rf"(?:^|[.?!]\s+)(?:(?:what|where|how|why|which|who|when)\s+)?(?:is|are|was|were|isn't|aren't|wasn't|weren't)\s+(?:\w+\s+){{1,4}}?{NOT}{P}\b[^.]*\?",
    ),
    (
        "have/get/keep + object + participle",
        rf"\b(?:have|has|had|having|get|gets|got|keep|keeps|kept|leave|want|wants|need|needs|make|makes|find)\s+{DET}\s+(?:\w+\s+){{1,2}}?{NOT}{P}\b",
    ),
    (
        "elliptical: if/when/as/once + participle",
        rf"\b(?:if|when|once|unless|until|as|while|although|though|where|than)(?:\s+(?:\w+ly|not|otherwise))*\s+{NOT}{P}\b",
    ),
    (
        "sentence-initial participle",
        rf"(?:^|[.;:!?]\s+|,\s+)(?:not\s+(?:to\s+be\s+)?)?{NOT}{P}\b(?=\s*(?:,|\b(?:by|for|in|on|with|to|at|after|before|from|under|during)\b))",
    ),
    (
        "need + -ing",
        r"\b(?:need|needs|needed|want|wants|require|requires)\s+(?!(?:nothing|something|anything|everything|bedding|clothing|counseling|training|nursing|screening)\b)\w{2,}ing\b",
    ),
    (
        "noun + participle + by/prep",
        rf"\b(?!(?:i|you|we|he|she|it|they|who|which|that|the|a|an|to|and|or|have|has|had|be|is|are|was|were)\b)\w+\s+(?:not\s+)?{NOT}{P}\s+(?:by|in|on|at|after|before|for|from|with|during|under|into|through|late|early)\b",
    ),
    ("thing + participle", rf"\b(?:anything|something|everything|nothing)\s+{NOT}{P}\b"),
    ("participle at end after object", rf"\b{DET}\s+\w+\s+{NOT}{P}\s*[.,;:)]"),
]
COMPILED = [(name, re.compile(p, re.I)) for name, p in PATTERNS]


def scan(text):
    text = text.replace("\u2019", "'").replace("*", " ").replace("`", " ")
    return [(name, m.group(0)) for name, rx in COMPILED for m in rx.finditer(text)]


def scan_file(path):
    resolved = validate_user_path(path, must_exist=True)
    assert_input_size(resolved)
    with open(resolved, encoding="utf-8") as handle:
        text = handle.read()
    return resolved, [
        (resolved, ln, name, frag.strip())
        for ln, line in enumerate(text.splitlines(), 1)
        for name, frag in scan(line)
    ]


def main(argv):
    if len(argv) < 2:
        print("Usage: python3 av_scan.py FILE [FILE ...]", file=sys.stderr)
        return 2
    exit_code = 0
    for arg in argv[1:]:
        try:
            resolved, hits = scan_file(arg)
        except PathValidationError as error:
            print("%s: %s" % (arg, error), file=sys.stderr)
            exit_code = 2
            continue
        for _resolved, ln, name, frag in hits:
            print("%s:%d: [%s] %s" % (resolved, ln, name, frag))
            exit_code = max(exit_code, 1)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
