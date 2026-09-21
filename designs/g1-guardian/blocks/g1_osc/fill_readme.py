"""Insert the results table (from mk_readme_table.py) and the corner verdict into README.md."""
import subprocess, re
txt = subprocess.check_output(["python3", "mk_readme_table.py"], text=True)
rows = [l for l in txt.splitlines() if l.startswith("| ") and "code" not in l.split("|")[6]]
fs = [float(l.split("|")[7]) for l in rows if l.split("|")[6].strip() == "8" and l.split("|")[4].strip() == "1.2"]
lo, hi = 0.777, 1.500   # trim ratios code 15 / code 0 relative to mid (tt, 27 C, revision 4), see table
allf = [float(l.split("|")[7]) for l in rows if l.split("|")[6].strip() == "8"]
bad = [f for f in allf if not (abs(f/10-1) <= 0.2 or lo*f <= 10.0 <= hi*f)]
verdict = "passed" if not bad else "failed (marginal: %d of %d points, fastest corner trims only to %.2f MHz)" % (len(bad), len(allf), min(bad)*lo)
r = open("README.md").read()
r = re.sub(r"### Results \(simulated\)\n.*?(?=## Design history)", "### Results (simulated)\n\n<!-- RESULTS -->\n\n", r, flags=re.S)
r = re.sub(r"\| Corners / temperature / supply \| .*? \|", "| Corners / temperature / supply | <!-- CORNERS --> |", r)
r = r.replace("<!-- RESULTS -->", txt.strip())
r = r.replace("<!-- CORNERS -->", verdict + "; mid trim, 1.2 V: %.2f to %.2f MHz" % (min(fs), max(fs)))
open("README.md", "w").write(r)
print(verdict, min(fs), max(fs))
