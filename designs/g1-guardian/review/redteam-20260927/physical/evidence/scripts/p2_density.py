# Global densities and the minimum / maximum 800x800 um window density on a 5 um grid (every window fully
# inside the 1414 um die) for every filled layer group, on r3. Same method as redteam-20260925 s8, all groups.
import pya, json, os
G = '/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r3.gds'
OUT = '${BULK}/redteam-20260927/physical/p2'; os.makedirs(OUT, exist_ok=True)
ly = pya.Layout(); ly.read(G); top = ly.cell('g1_chip_top'); dbu = ly.dbu
class Rcv(pya.TileOutputReceiver):
    def __init__(self): self.d = {}
    def put(self, ix, iy, tile, obj, dbu, clip): self.d[(ix, iy)] = obj
T = 5.0; N = 283
groups = {'Activ': [(1,0),(1,22)], 'GatPoly': [(5,0),(5,22)], 'M1': [(8,0),(8,22)], 'M2': [(10,0),(10,22)],
          'M3': [(30,0),(30,22)], 'M4': [(50,0),(50,22)], 'M5': [(67,0),(67,22)], 'TM1': [(126,0),(126,22)], 'TM2': [(134,0),(134,22)]}
lim = {'Activ': (25, 65, 35, 55), 'GatPoly': (None, None, 15, None), 'M1': (25, 75, 35, 60), 'M2': (25, 75, 35, 60), 'M3': (25, 75, 35, 60),
       'M4': (25, 75, 35, 60), 'M5': (25, 75, 35, 60), 'TM1': (None, None, 25, 70), 'TM2': (None, None, 25, 70)}
out = {}
for g, lays in groups.items():
    tp = pya.TilingProcessor(); tp.threads = int(os.environ.get('NTHR', '8')); tp.tile_size(T, T); tp.tile_origin(0, 0); tp.tiles(N, N); tp.dbu = dbu
    nm = []
    for i, (l, d) in enumerate(lays):
        li = ly.find_layer(l, d)
        if li is None: continue
        tp.input('a%d' % i, pya.RecursiveShapeIterator(ly, top, li)); nm.append('a%d' % i)
    rc = Rcv(); tp.output('o', rc); tp.queue('_output(o, to_f(((' + '+'.join(nm) + ') & _tile).area))'); tp.execute(g)
    P = [[0.0] * (N + 1) for _ in range(N + 1)]
    for i in range(N):
        for j in range(N):
            P[i+1][j+1] = P[i][j+1] + P[i+1][j] - P[i][j] + rc.d.get((i, j), 0.0)
    W = 160; best = (1e9, 0, 0); worst = (-1, 0, 0)
    for x in range(0, 1414 // 5 - W + 1):
        for y in range(0, 1414 // 5 - W + 1):
            a = P[x+W][y+W] - P[x][y+W] - P[x+W][y] + P[x][y]
            d = a * dbu * dbu / 640000.0
            if d < best[0]: best = (d, x * 5, y * 5)
            if d > worst[0]: worst = (d, x * 5, y * 5)
    glob = P[N][N] * dbu * dbu / (1414.0 * 1414.0)
    out[g] = dict(global_pct=round(100 * glob, 4), win_min_pct=round(100 * best[0], 3), win_min_at=best[1:],
                  win_max_pct=round(100 * worst[0], 3), win_max_at=worst[1:], limits_win_min_max_glob_min_max=lim[g])
    print(g, out[g], flush=True)
json.dump(out, open(OUT + '/density_win5um.json', 'w'), indent=1)
