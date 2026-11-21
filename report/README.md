# EE289 checkpoint report

- `checkpoint.pdf`: the file to submit on Canvas (generated from `checkpoint.md`).
- `checkpoint.md`: source. Rebuild after edits:
  `pandoc checkpoint.md -s --css style.css --embed-resources -o checkpoint.html`, then print
  `checkpoint.html` to PDF from any browser (Letter, background graphics on).
- `make_figure.py`: regenerates `fig_stages_compact.png` from a `summary.csv`.

Results in Section 3 are from the **two-laptop testbed** run (`results/summary.csv`, `results/raw.csv`);
the simulated run in `results/simulated/` is a cross-check. Figure: 
`python report/make_figure.py results/summary.csv report/fig_stages_real.png`.

## Checkpoint requirements → report sections

| Checkpoint requirement | Where it is covered | Status |
| --- | --- | --- |
| Project title and team member names | Title block | Done |
| 1. Current question and scope, incl. approved changes | §1 (question, scope, changes table) | Done; Windows change stated plainly as made, not yet approved |
| 2. Work completed since Proposal v2 | §2 | Done |
| 3. At least one preliminary result; what it shows and does not establish | §3: payload table, latency table, Figure 1, "What it shows", "What it does not yet establish" | Done (two-laptop testbed measurements) |
| 4. Challenges, blockers, open questions, risks | §4 risk table + open question | Done |
| 5. Remaining tasks and realistic timeline to presentation and report | §5 timeline (Nov 21 – Dec 14) | Done |
| 6. Evidence that proposal feedback was considered | §6: each of the four feedback points with the response | Done |
| 7. Contributions (two-person teams) | §7 | Individual project, one line |
| ~2–3 pages | PDF is about 3.5 pages incl. references | Done |
| Cite external materials | References | Done (proposal refs 6 and 7 dropped: ref 7 reuses ref 4's DOI) |
| Acknowledge substantial AI assistance | "AI assistance" section | Done; review wording |
| Single PDF via Canvas | `checkpoint.pdf` | Kevin submits |
