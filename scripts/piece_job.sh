#!/bin/bash
# One-piece render job for collection runs (one piece per cloud machine). usage: KIT=<frozen kit> OUT=<shared folder> bash piece_job.sh <piece>
# Runs: setup check, mesh + casting checks (bodies, thickness, stones, settings/clipping), 4-view square, web GLB.
# Never on a Mac. Writes only its own files under $OUT/{squares,reports,glb}/.
set -u
P=$1; B=${OUT:?set OUT to the shared output folder}; KITSRC=${KIT:?set KIT to the frozen kit folder}
if [ "$(uname -s)" = "Darwin" ]; then echo "refusing: cloud machines only"; exit 3; fi
python3 -c "import bpy, numba, trimesh, manifold3d, skimage, scipy" 2>/dev/null || pip install -q bpy==5.3.0 numpy scipy scikit-image trimesh manifold3d pillow numba rtree
K=/tmp/piecekit; rm -rf "$K"; cp -r "$KITSRC" "$K"
export NUMBA_CACHE_DIR=/tmp/nbcache
cd "$K" && python3 codeversion.py check CODE_VERSION.txt || { echo "code changed since freeze: stop and tell the owner thread"; exit 4; }
mkdir -p $B/squares $B/reports $B/glb /tmp/piece_out
R=$B/reports/$P.txt
case $P in *cuff*) TO=3000; VOXO=0.05;; *) TO=2400; VOXO=0.045;; esac
{
echo "== $P  $(date -u +%FT%TZ)  $(hostname)"
for V in $VOXO $(python3 -c "print($VOXO*0.95, $VOXO*1.06)"); do      # re-mesh at a shifted voxel until watertight (once round)
  rm -f /tmp/piece_out/*.stl
  OUTDIR=/tmp/piece_out VOX=$V timeout $TO python3 make.py $P stl 2>&1 | grep -E "bodies|debris|error|Error"
  python3 check.py /tmp/piece_out 2>&1 | grep "^$P" | sed 's/np.float64(\([0-9.]*\))/\1/g'
  grep -q '"watertight": true' /tmp/piece_out/checks.json && { VOXO=$V; echo "VOX $V watertight"; break; }
  echo "VOX $V not watertight, retrying"
done
python3 check_stones.py --jewelry /tmp/piece_out/$P.json 2>&1 | tail -n +1
python3 check_settings.py /tmp/piece_out/$P.stl /tmp/piece_out/$P.json 2>&1 | tail -n 40; echo "settings exit $?"
} > "$R" 2>&1
OUTSQ=$B/squares KIT_DIR="$K" TO=$TO VOXO=$VOXO PY=python3 WORK=/tmp/piece_rw bash "$K/render_square.sh" $P >> "$R" 2>&1
OUTDIR=/tmp/piece_out VOX=$VOXO GLBFACES=120000 timeout 1200 python3 make.py $P glb 2>&1 | grep -E "^glb|rror" >> "$R"
cd /tmp/piece_out && timeout 600 npx -y @gltf-transform/cli@4.1.1 optimize $P.glb $B/glb/$P-v${GLBV:-1}-lite.glb --compress meshopt >> "$R" 2>&1
ls -la $B/squares/$P.jpg $B/glb/$P-v${GLBV:-1}-lite.glb >> "$R" 2>&1
echo "== done $(date -u +%FT%TZ)" >> "$R"
cat "$R"
