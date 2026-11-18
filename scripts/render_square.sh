#!/bin/bash
# Render one piece to a 4-view Instagram square (hero + 3 angles) and keep the full build log.
# usage: bash render_square.sh <piece>
# env: OUTSQ  output folder for squares (default ./squares)
#      TO     timeout in seconds (default 2400; cuffs 3000)
#      VOXO   voxel size in mm (default 0.045; cuffs 0.05)
#      PRESO  render resolution per view (default 720)   PSPPO  samples (default 24)
#      PY     python with bpy 5.3 + numba (default python3)   WORK  scratch dir (default /tmp/mb_rw)
#      KIT_DIR  folder holding make.py and the kit (default: scripts/kit next to this file)
set -u
n=$1
# Never render on the client's own computer (a Mac): renders run on cloud machines, or a render farm for big jobs.
if [ "$(uname -s)" = "Darwin" ] && [ -z "${ALLOW_LOCAL_RENDER:-}" ]; then
  echo "refusing to render on a Mac: run this on a cloud machine (or a farm). ALLOW_LOCAL_RENDER=1 only if the owner asked for it."; exit 3
fi
D=${KIT_DIR:-$(cd "$(dirname "$0")/kit" && pwd)}
W=${WORK:-/tmp/mb_rw}; PY=${PY:-python3}; mkdir -p "$W"
OQ=${OUTSQ:-$PWD/squares}; mkdir -p "$OQ/_logs"
[ -f "$OQ/$n.jpg" ] && { echo "$n exists, skipping"; exit 0; }
V=${VOXO:-0.045}
cd "$D"
OUTDIR=$W VOX=$V PRES=${PRESO:-720} PSPP=${PSPPO:-24} timeout ${TO:-2400} "$PY" make.py "$n" local4 > "$OQ/_logs/$n.txt" 2>&1
# the bodies / weight / debris lines are the casting check: report them every time
r=$(grep -i -E "error| g \[|bodies|debris" "$OQ/_logs/$n.txt" | tr '\n' ' ')
echo "$n $r" >> "$W/_log.txt"; echo "$n $r"
"$PY" -c "
import sys; sys.path.insert(0,'$D')
from square import compose
from PIL import Image
v=[Image.open('$W/$n'+'_v000%d.png'%i).convert('RGBA') for i in range(1,5)]
compose(v,'$OQ/$n.jpg')
" 2>>"$W/_err.txt"
rm -f "$W/${n}"_v000*.png
