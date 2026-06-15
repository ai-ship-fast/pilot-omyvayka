import sys
from collections import deque
import numpy as np
from PIL import Image

def clean(inp, outp):
    img = Image.open(inp).convert("RGBA")
    a = np.array(img)
    h, w = a.shape[:2]
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    sat = mx - mn
    cand = (sat <= 30) & (mx >= 190)        # light, low-saturation (checker or white text)
    gray = cand & (mx >= 205) & (mx <= 243)  # the gray checker squares
    white = cand & (mx >= 248)               # white squares / solid white

    visited = np.zeros((h, w), dtype=bool)
    remove = np.zeros((h, w), dtype=bool)
    candf = cand  # local ref

    for sy in range(h):
        row = candf[sy]
        for sx in range(w):
            if not row[sx] or visited[sy, sx]:
                continue
            # BFS this component
            comp = []
            dq = deque([(sy, sx)])
            visited[sy, sx] = True
            gcount = wcount = 0
            touches_border = False
            while dq:
                y, x = dq.popleft()
                comp.append((y, x))
                if gray[y, x]: gcount += 1
                if white[y, x]: wcount += 1
                if x == 0 or y == 0 or x == w-1 or y == h-1:
                    touches_border = True
                for ny, nx in ((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
                    if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and candf[ny, nx]:
                        visited[ny, nx] = True
                        dq.append((ny, nx))
            area = len(comp)
            gfrac = gcount / area
            wfrac = wcount / area
            is_checker = (gfrac > 0.12 and wfrac > 0.12)  # alternating gray+white => checkerboard
            if touches_border or is_checker:
                for (y, x) in comp:
                    remove[y, x] = True

    a[:, :, 3] = np.where(remove, 0, a[:, :, 3])

    ys, xs = np.where(a[:, :, 3] > 0)
    pad = 10
    y0, y1 = max(0, ys.min()-pad), min(h, ys.max()+pad)
    x0, x1 = max(0, xs.min()-pad), min(w, xs.max()+pad)
    out = Image.fromarray(a[y0:y1, x0:x1])
    out.save(outp)
    print(outp, "size", out.size, "removed%", round(100*remove.sum()/(h*w),1))

base = sys.argv[1]
clean(base + r"\canister.png", base + r"\canister-clean.png")
clean(base + r"\bottle.png",   base + r"\bottle-clean.png")
