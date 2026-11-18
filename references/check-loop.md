# The make-and-check loop

Render, compare against the named references, list what's off, fix, repeat until it holds up. Show the client only results that passed.

## Each pass
1. Read the build log (`_logs/<piece>.txt`): bodies, grams, size, dropped debris, errors.
2. Open the square next to two or three reference images, one per lead influence.
3. Write what reads robotic, specifically and by location ("upper-left wing: two stones touch"; "leading edge: eight evenly spaced beads"). Note which shared function causes it if you can tell (for example `vein_wing`, `hyo_flourish`, `_clipbar`, the claw/seat cut).
4. Decide: is it this piece's seed, or the shared generator? Shared problems are fixed once, centrally, then every affected piece re-renders.
5. Re-render and check again. Stop when the list is empty or only has taste calls for the client.

## Report format (one per piece)
```
<piece>: bodies N, X.X g, size [..] mm, watertight yes/no
Passes: what matches the references
Robotic: 1) ... 2) ... 3) ...
Casting: anything under 0.8 mm, loose bits, odd stone sizes
Shared-code cause (if known): ...
```

## Flags that kept coming back
| Flag | Usual cause | Fix |
|---|---|---|
| Even-width veins and rims | stroke helper with constant radius | width keys that swell and taper (`wisp.organic()` on) |
| Ball ends | sphere terminal | ribbon `ends` to a needle |
| Bead row, ladder ticks, dot rows, milgrain | evenly spaced barbs or notches, `bead_row`, `grain=True` | remove, or randomise spacing and size; `grain=False` |
| Loose chips near stones | seat cut severs a claw tip | move the seat or shorten the cut; re-mesh and count bodies |
| Straight rods through a body | clip bar or pin builder | fold the bar into the form |
| Stones touching or in a grid | packer spacing too tight | wall between seats, varied sizes |
| Same silhouette across a family | seed only drives stones | let the seed drive the layout |
| Stone invisible in renders | clear glass on white, or hidden by metal | darker bezel edge, more absorption, or move the stone |
| Cropped thumbnail | compose margin | re-frame that view |
