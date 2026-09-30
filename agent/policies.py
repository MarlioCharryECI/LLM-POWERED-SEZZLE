"""Policy corpus loader.

The entire policy base is 12 short markdown docs (~2k tokens total). At that
size, retrieval is a solved problem: we load ALL of it into the prompt every
call and rely on prompt caching for cost. No chunking, no embeddings, no vector
store — those would add infrastructure and a recall failure mode (e.g. the
"missed a payment, can I reschedule?" case needs the rescheduling AND the
failed-payments doc at once, exactly where top-k retrieval silently drops one).

See DECISIONS.md #1 for the breakpoint at which this choice flips to BM25/embeddings.
"""

from functools import lru_cache
from pathlib import Path

POLICY_DIR = Path(__file__).resolve().parent.parent / "data" / "policies"


@lru_cache(maxsize=1)
def load_policies() -> str:
    """Return all policy docs concatenated into one prompt-ready block.

    Files are read in sorted filename order (01..12) so the block is
    deterministic — the same bytes every run, which keeps prompt caching stable
    and makes the system prompt reproducible.
    """
    files = sorted(POLICY_DIR.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"no policy files found in {POLICY_DIR}")
    sections = []
    for f in files:
        text = f.read_text(encoding="utf-8").strip()
        # Tag each doc with its source filename so the model can cite it and so
        # answers are traceable back to a specific policy.
        sections.append(f"<policy source=\"{f.name}\">\n{text}\n</policy>")
    return "\n\n".join(sections)


if __name__ == "__main__":
    block = load_policies()
    print(f"loaded {block.count('<policy ')} policies, {len(block)} chars")
