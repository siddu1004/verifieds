1. Run make verify. Fix every failure at its cause, not by loosening a check.
2. Run git diff --stat and confirm only the planned files changed.
3. Search the diff for TODO, FIXME, pass-only bodies, commented-out code and unused symbols. Remove them.
4. Report each acceptance item mapped to the test that proves it.
