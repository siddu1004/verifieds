# Board

| Node | Task ID | Title | Deps | State | Iter | Evidence | CI |
|---|---|---|---|---|---|---|---|
| N0 | R-05 | N0 BOOT | none | done | 0 | exit0 | success |
| N1 | S-02 | N1 S-02 scheduler engine | N0 | done | 0 | exit0 | success |
| N2 | S-03 | N2 S-03 CLI | N1 | done | 0 | exit0 | success |
| N3 | S-05 | N3 S-05 detector | N1 | done | 0 | exit0 | success |
| N4 | S-06 | N4 S-06 harness | N1, N2 | done | 0 | exit0 | success |
| N5 | S-08 | N5 S-08 pipeline | N3, N4 | done | 0 | exit0 | success |
| N6 | S-09 | N6 S-09 MCP server | N5 | done | 0 | exit0 | success |
| N7 | S-10 | N7 S-10 safety | N6 | pending | 0 | none | none |
| N8 | S-11 | N8 S-11 study | N5 | pending | 0 | none | none |
| N9 | S-12 | N9 S-12 docs | N7, N8 | pending | 0 | none | none |
| N10 | RELEASE | N10 RELEASE | N9 | pending | 0 | none | none |
