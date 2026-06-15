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
    # checkerboard = light, low-saturation (white + light-gray squares)
    bgcand = (sat <= 26) & (mx >= 165)

    # sample corners for reporting
    corners = [tuple(a[0,0][:3]), tuple(a[0,w-1][:3]), tuple(a[h-1,0][:3]), tuple(a[h-1,w-1][:3])]

    bg = np.zeros((h, w), dtype=bool)
    dq = deque()
    for x in range(w):
        for y in (0, h-1):
            if bgcand[y, x] and not bg[y, x]:
                bg[y, x] = True; dq.append((y, x))
    for y in range(h):
        for x in (0, w-1):
            if bgcand[y, x] and not bg[y, x]:
                bg[y, x] = True; dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for ny, nx in ((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
            if 0 <= ny < h and 0 <= nx < w and not bg[ny, nx] and bgcand[ny, nx]:
                bg[ny, nx] = True; dq.append((ny, nx))

    # dilate bg by 1px into light fringe pixels to kill halo
    fringe = (sat <= 40) & (mx >= 150)
    bd = bg.copy()
    bd[1:,:]  |= bg[:-1,:]; bd[:-1,:] |= bg[1:,:]
    bd[:,1:]  |= bg[:,:-1]; bd[:,:-1] |= bg[:,1:]
    grow = bd & ~bg & fringe
    bg |= grow

    a[:, :, 3] = np.where(bg, 0, a[:, :, 3])

    ys, xs = np.where(a[:, :, 3] > 0)
    pad = 10
    y0, y1 = max(0, ys.min()-pad), min(h, ys.max()+pad)
    x0, x1 = max(0, xs.min()-pad), min(w, xs.max()+pad)
    out = Image.fromarray(a[y0:y1, x0:x1])
    out.save(outp)
    print(outp, "size", out.size, "corners", corners, "removed%", round(100*bg.sum()/(h*w),1))

base = sys.argv[1]
clean(base + r"\canister.png", base + r"\canister-clean.png")
clean(base + r"\bottle.png",   base + r"\bottle-clean.png")
