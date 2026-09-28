# Read GDSII header records (HEADER, BGNLIB, LIBNAME, UNITS) and count structures; flags the KLayout context cell.
import struct, sys, json
def scan(p):
    r = {"file": p.split("/")[-1]}; nstr = 0; ctx = False
    with open(p, "rb") as f:
        data = f.read()
    i = 0
    while i < len(data):
        ln, rt, dt = struct.unpack(">HBB", data[i:i+4]); body = data[i+4:i+ln]
        if rt == 0x00: r["gds_version"] = struct.unpack(">h", body)[0]
        elif rt == 0x01: r["bgnlib_timestamps"] = list(struct.unpack(">12h", body))
        elif rt == 0x02: r["libname"] = body.rstrip(b"\0").decode()
        elif rt == 0x03:
            def r8(b):
                s = -1 if b[0] & 0x80 else 1; e = (b[0] & 0x7f) - 64; m = int.from_bytes(b[1:], "big")
                return s * m / (1 << 56) * 16.0 ** e
            r["units_user_per_db"], r["units_m_per_db"] = r8(body[:8]), r8(body[8:])
        elif rt == 0x05: nstr += 1
        elif rt == 0x06 and body.rstrip(b"\0") == b"$$$CONTEXT_INFO$$$": ctx = True
        if ln == 0: break
        i += ln
    r["structures"] = nstr; r["klayout_context_cell"] = ctx; r["bytes"] = len(data)
    return r
print(json.dumps([scan(p) for p in sys.argv[1:]], indent=1))
