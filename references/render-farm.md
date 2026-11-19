# Rendering in bulk

One render uses every core, so bulk rendering is split: one piece per machine, never several in parallel on one box. Don't render on a personal laptop; use cloud machines, or a render farm for animations.

## Settings that held up
| Pieces | Timeout (TO) | Voxel (VOXO) | Resolution | Samples |
|---|---|---|---|---|
| Rings, ear pieces, studs, clips, pendants, necklaces | 2400 s | 0.045 mm | 720 per view | 24 |
| Cuffs (larger) | 3000 s | 0.05 mm | 720 | 24 |
| Furniture scale (cm units) | per view | 0.09 cm (0.3 for a quick mesh check) | 900 | 24 |

A small piece (under 25 mm) automatically meshes at 0.6x the voxel size.

## Freeze, render, collect, fix, bump
1. **Freeze.** `python scripts/codeversion.py freeze r4 kit/*.py render_square.sh > CODE_VERSION.txt`.
2. **Hand out jobs.** One piece per machine, with the piece name, output folder, TO, VOXO and the influence notes it should be checked against. Write the table into a `RENDER_JOBS.md`.
3. **Every job checks the freeze first** (`python scripts/codeversion.py check CODE_VERSION.txt`). If files changed without a version bump, the job waits. A square from older code is stale.
4. **Jobs never edit shared files.** Other machines import them. A job renders, runs the check loop on its own square, and reports flags.
5. **One owner fixes centrally.** Collect the reports, find the shared causes, fix once, then bump (`r4-fix1`, `r4-fix2`, `r4-fix3`) with new checksums and name exactly which pieces re-render.
6. **Keep the full log.** `render_square.sh` writes the whole `make.py` output, including the bodies line, to `<OUTSQ>/_logs/`. Move failed squares to `_flagged/` and keep the pre-fix squares in `_pre_fixN/` so you can compare.

## Lessons
- A fix can regress something else. In one round, new feathered barbs fixed "plain wings" and created evenly spaced ticks that read as bead rows on 20+ pieces. Check the first few re-renders before releasing the whole batch.
- Missing dependencies stall every job at once (`numba` was left out of the setup line once). Test the setup line on a clean machine before fanning out.
- The render script skips a piece whose square already exists. Delete or move stale squares before a re-render.
- Earring pairs report two bodies. Write that into the check so render jobs don't flag it.

- Parallel machines on a shared mount: set NUMBA_CACHE_DIR=/tmp/nbcache (machine-local). Several machines compiling into the shared __pycache__ at once leave truncated cache files and the run fails with "_pickle.UnpicklingError: pickle data was truncated" (Nov 19).
