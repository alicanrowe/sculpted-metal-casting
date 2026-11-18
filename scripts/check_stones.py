"""Stone sourcing check: is every stone in a piece something you can actually buy?

    python check_stones.py --jewelry <pieces.json ...>      stones in mm (jewelry kit units)
    python check_stones.py --furniture-cm <pieces.json ...> stones in cm (furniture kit units, x10 to mm)

Each json holds {"stones": [{"kind", "D", "L"?, "shape"?}, ...]} (make.py / sawmoth.py write this).
For each stone it prints the size in mm, an approximate carat weight, and a verdict:
  OK        stock calibrated size, easy to buy
  LARGE     sold, but as a one-off "collector" stone, not calibrated stock: price and match are a problem
  NO        not realistically obtainable faceted at that size and species, swap it
plus a suggested buyable swap. Sizes and price bands are rough sourcing guidance (Nov 2026), not quotes."""
import sys, json, math

# species: (specific gravity, largest common calibrated faceted size mm, largest realistic one-off mm, rough $/ct band, note)
SPECIES = {
    "amethyst":   (2.65, 20, 40, "1-10", "quartz: large clean faceted stones are common and cheap"),
    "citrine":    (2.65, 20, 40, "1-10", "quartz (mostly heated amethyst): large sizes common"),
    "topaz":      (3.53, 18, 35, "1-8", "sky/swiss blue topaz (treated): large sizes common and cheap"),
    "londonblue": (3.53, 16, 30, "2-15", "london blue topaz (treated): fine up to ~16 mm stock, bigger as one-offs"),
    "aquamarine": (2.70, 10, 18, "15-300", "price climbs steeply with size and colour; big clean stones are costly"),
    "garnet":     (3.95, 10, 14, "5-60", "almandine/rhodolite: stock to ~10 mm, larger goes nearly black and rare"),
    "moonstone":  (2.57, 8, 14, "5-40", "usually cut as cabochon; faceted rainbow moonstone is sold small"),
    "labradorite": (2.70, 10, 20, "2-20", "almost always cabochon, not faceted"),
    "peridot":    (3.34, 8, 14, "10-80", "stock to ~8 mm"),
}
SWAP = {
    "aquamarine": "sky blue topaz (same colour, cheap in large sizes) or keep aquamarine at 10 mm or less",
    "garnet": "rhodolite at 10 mm or less, or lab-grown ruby for a large red",
    "moonstone": "a moonstone cabochon, or faceted rock crystal for sparkle",
    "londonblue": "london blue topaz at 16 mm or less, or deep blue lab spinel",
    "labradorite": "a labradorite cabochon",
}
CALIB = {"round": [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20],
         "oval": [(5, 3), (6, 4), (7, 5), (8, 6), (9, 7), (10, 8), (12, 10), (14, 10), (16, 12), (18, 13), (20, 15)],
         "pear": [(4, 3), (5, 3), (6, 4), (7, 5), (8, 6), (9, 7), (10, 8), (12, 8)],
         "marquise": [(4, 2), (5, 2.5), (6, 3), (7, 3.5), (8, 4), (10, 5), (12, 6)]}


def carat(L, W, sg):
    """Rough faceted weight: volume of a 60%-depth brilliant scaled by specific gravity."""
    return 0.0061 * L * W * (0.6 * W) * sg / 3.52


def check(stone, scale=1.0):
    k = stone["kind"]; D = float(stone["D"]) * scale; L = float(stone.get("L") or stone["D"]) * scale
    L, W = max(L, D), min(L, D)
    sg, common, rare, band, note = SPECIES.get(k, (3.0, 8, 12, "?", "unknown species: check with the dealer"))
    ct = carat(L, W, sg)
    v = "OK" if L <= common else ("LARGE" if L <= rare else "NO")
    return dict(kind=k, size_mm=f"{L:g}x{W:g}" if abs(L - W) > 0.05 else f"{W:g}", ct=round(ct, 1), verdict=v,
                usd_per_ct=band, note=note, swap=(SWAP.get(k, "a smaller stock size") if v != "OK" else ""))


if __name__ == "__main__":
    scale = 10.0 if "--furniture-cm" in sys.argv else 1.0
    worst = "OK"
    for p in [a for a in sys.argv[1:] if not a.startswith("--")]:
        d = json.load(open(p)); st = d.get("stones", []) if isinstance(d, dict) else []
        print(f"== {p}")
        for s in st if isinstance(st, list) else []:
            r = check(s, scale)
            print(f"  {r['verdict']:5s} {r['kind']:11s} {r['size_mm']:>8s} mm  ~{r['ct']} ct  (${r['usd_per_ct']}/ct)  {r['swap']}")
            if r["verdict"] == "NO" or (r["verdict"] == "LARGE" and worst == "OK"): worst = r["verdict"]
    print("worst:", worst)
