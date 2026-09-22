# ------------------------------------------------------------------ resistor array ---------
def unit(c, r):
    D.pcell('rppd', {'Calculate': 'R', 'w': '%gu' % RW, 'l': '%gu' % RL, 'b': 0}, colx(c), rowy(r))
def dummy(c, r):
    D.box('GatPoly', colx(c), rowy(r) + 0.25, colx(c) + RW, rowy(r) + RL - 0.25)   # inside SalBlock (Sal.c 0.2)
def strap(c, r, side):   # join the heads of columns c and c+1 on `side`
    if side == 'top':
        y = rowy(r) + RL
        D.box('M1', colx(c) + 0.02, y + 0.13, colx(c + 1) + RW - 0.02, y + HEAD)
    else:
        y = rowy(r)
        D.box('M1', colx(c) + 0.02, y - HEAD, colx(c + 1) + RW - 0.02, y - 0.13)
def chain(r, c0, n):
    """meander of n units from column c0 (straps alternate bot/top starting at the bottom).
    Returns ((c_first, side), (c_last, side)) of the two free heads."""
    for u in range(n):
        unit(c0 + u, r)
        if u > 0:
            strap(c0 + u - 1, r, 'bot' if (u - 1) % 2 == 0 else 'top')
    first = (c0, 'top')
    last = (c0 + n - 1, 'top' if n % 2 == 0 else 'bot')
    return (first, last)
def covers(r, c_first, c_last):
    x1, x2 = colx(c_first), colx(c_last) + RW
    y1, y2 = rowy(r), rowy(r) + RL
    D.box('pSD', x1 - 0.18, y1 - 0.61, x2 + 0.18, y2 + 0.61)
    D.box('EXTBlock', x1 - 0.18, y1 - 0.61, x2 + 0.18, y2 + 0.61)
    D.box('SalBlock', x1 - 0.20, y1, x2 + 0.20, y2)
# row 0 (south): [d d][RD2 a 13][R2N a 10][R1N][R1P][R2P a 10][RD2 b 13][d d]
for c in (0, 1, 50, 51): dummy(c, 0)
RD2a = chain(0, 2, 13); R2Na = chain(0, 15, 10); R1N = chain(0, 25, 1); R1P = chain(0, 26, 1)
R2Pa = chain(0, 27, 10); RD2b = chain(0, 37, 13)
# row 1 (north): [d d][RD2 c 13][R2P b 10][RD1 2][R2N b 10][RD2 d 12][d][d d]
for c in (0, 1, 49, 50, 51): dummy(c, 1)
RD2c = chain(1, 2, 13); R2Pb = chain(1, 15, 10); RD1 = chain(1, 25, 2); R2Nb = chain(1, 27, 10); RD2d = chain(1, 37, 12)
for r in range(2):
    covers(r, 0, NCOL - 1)
AX1 = colx(NCOL - 1) + RW                            # array east edge (bodies)
AY1 = rowy(1) + RL

# ------------------------------------------------------------------ gap tracks ----------------
# gap g: 0 below row 0, 1 between the rows, 2 above row 1; track i counts away from row 0
def gap_track(g, i):
    if g == 0:
        return rowy(0) - HEAD - 0.5 - i * TRACK
    if g == 1:
        return rowy(0) + RL + HEAD + 0.5 + i * TRACK
    return rowy(1) + RL + HEAD + 0.5 + i * TRACK
def to_track(c, r, side, g, i):
    """head (top/bottom) of column c, row r -> Metal3 drop to track i of gap g; returns (x, y_track)."""
    x = colx(c) + RW / 2
    y = rowy(r) + RL + 0.28 if side == 'top' else rowy(r) - 0.28
    D.stack(x, y, 'M1', 'M3')
    yt = gap_track(g, i)
    D.vwire('M3', x, y, yt, EXTW)
    D.sq('M3', x, yt, PAD); D.sq('Via2', x, yt, VIA); D.sq('M2', x, yt, PAD)
    return (x, yt)
def to_channel(net, x, y):
    """Metal2 horizontal from (x, y) west to the channel vertical of `net`, Via2 there."""
    xc = CHX[net]
    D.hwire('M2', xc, x, y, EXTW)
    D.sq('M2', xc, y, PAD); D.sq('Via2', xc, y, VIA); D.sq('M3', xc, y, PAD)
    return (xc, y)
chan_y = {k: [] for k in CH}
def reg(net, y):
    chan_y[net].append(y)
def link(a, b):
    """two heads in the same gap joined by one track: a, b = (col, row, side, gap, track)"""
    x1, yt = to_track(*a); x2, _ = to_track(*b)
    D.hwire('M2', x1, x2, yt, EXTW)
    return (min(x1, x2), yt)
# gap 0: sense_n (R1N bottom), sense_p (R1P bottom) east; RD2 a/b link
xn, ytn = to_track(25, 0, 'bot', 0, 0); xp, ytp = to_track(26, 0, 'bot', 0, 1)
link((14, 0, 'bot', 0, 2), (49, 0, 'bot', 0, 2))
# gap 1: vn = R1N top + R2N a first; vp = R1P top + R2P a first; x2n = R2N a last; x2p = R2P a last;
#        vped_ref = RD2 a first; RD2 b last (top) <-> RD2 c last (row 1 bottom)
x, yt = link((25, 0, 'top', 1, 0), (15, 0, 'top', 1, 0)); reg('vn', to_channel('vn', x, yt)[1])
x, yt = link((26, 0, 'top', 1, 1), (27, 0, 'top', 1, 1)); reg('vp', to_channel('vp', x, yt)[1])
x, yt = to_track(24, 0, 'top', 1, 2); reg('x2n', to_channel('x2n', x, yt)[1])
x, yt = to_track(36, 0, 'top', 1, 3); reg('x2p', to_channel('x2p', x, yt)[1])
x, yt = to_track(2, 0, 'top', 1, 4); reg('vped_ref', to_channel('vped_ref', x, yt)[1])
link((37, 0, 'top', 1, 5), (14, 1, 'bot', 1, 5))
# gap 2: x2n = R2N b first; isense = R2N b last; x2p = R2P b first; vped = R2P b last;
#        vref_buf = RD1 first; vped_ref = RD1 last; RD2 c first <-> RD2 d first; vss = RD2 d last
x, yt = to_track(27, 1, 'top', 2, 0); reg('x2n', to_channel('x2n', x, yt)[1])
x, yt = to_track(36, 1, 'top', 2, 1); reg('isense', to_channel('isense', x, yt)[1])
x, yt = to_track(15, 1, 'top', 2, 2); reg('x2p', to_channel('x2p', x, yt)[1])
x, yt = to_track(24, 1, 'top', 2, 3); reg('vped', to_channel('vped', x, yt)[1])
x, yt = to_track(25, 1, 'top', 2, 4); reg('vref_buf', to_channel('vref_buf', x, yt)[1])
x, yt = to_track(26, 1, 'top', 2, 5); reg('vped_ref', to_channel('vped_ref', x, yt)[1])
link((2, 1, 'top', 2, 6), (37, 1, 'top', 2, 6))
x, yt = to_track(48, 1, 'top', 2, 7); reg('vss', to_channel('vss', x, yt)[1])

