# C01 PROBE CLASSIFICATION (PROVISIONAL)

Task C01: single controlled ngspice-46 run on the sealed V8 transient copy with
ONLY save additions (savecurrents-equivalent via verified selectors; no
topology/value/model/supply/temperature/stimulus/timestep/load change).

## Run identity
- deck: NGSPICE46-...-SOURCE-DECK-V8-TRAN-2P5G-C01.cir (sha256 09cb1b8ce26b0ef60ee89a4258344635b2c0bfbc4d96fd72e3ff1f76e081c51f)
- interface (unchanged copy): sha256 68b1bc654f4449e63958f7dd0e82154aa54f8d3fd39725ec1dc74834876053b2
- ngspice: ngspice-46 binary sha256 6aacaca88f656e5e19074ac070fb410bf6cc437df1de88ec28d50a24c6239a1b
- invocation: ngspice -b -o <C01-RUN.log> <C01 deck>; cwd = C01 project dir
- RC 0, 1065 data rows (identical to baseline), 0 warnings/errors
- C01 raw: raw_tb_p1_cml2lv_hybrid_tran_2p5g_v8.raw sha256 5ebd09ff96dc6aabe3b20fda571f6bb0baa2db38573c712d7344a0575e9ce176 (89 vars)
- baseline raw (sealed): sha256 dbab1bd80ddaed8c3bee8f0c5ca816ac192fb687a7c31e841c1de46a7f68906c (78 vars)

## Verification (CONFIRMED)
- All 78 baseline variables bit-identical in the C01 raw (0 mismatches over 1065 rows);
  time axis identical; the added saves changed the simulation NOTHING.
- 11 device-current vectors saved (BJT q.xu1.xqef_p/qef_n.qnpn13g2 ic/ib/ie;
  MOS n.xu1.xm1/xm2/xmtail.nsg13_lv_nmos[ids], n.xu1.xm3/xm4.nsg13_lv_pmos[ids]).
- 10 cml_diff crossings at 63.26/263.26/.../1863.26 ps (every 200 ps); zero 0.6 V
  CMOS-output crossings (reproduces the sealed V8 fact).

## Swing evidence (2 ns full range)
- input cml single-ended swing 0.5772 V (differential 1.154 V pk-pk)
- ef_p swing 0.5503 V (0.370..0.920 V)  -> compression ef/input = 0.953
- gp swing 0.2173 V (0.150..0.367 V)    -> compression gp/ef = 0.395 (== design
  divider ratio R2/(R1+R2) = 14.5/36.5 = 0.397; a STATIC attenuation)
- cm_n swing 0.0680 V                    -> compression cm/gp = 0.313
- cmos_out_n swing 0.0007 V, cmos_out_p swing 0.00005 V (latched; never switch)

## Current evidence (full range; at-crossing values in C01-CROSSING-TABLE.tsv)
- follower collector currents alternate ~57-78 uA at the crossings (range 28-108 uA)
- divider/follower path currents ~60-80 uA
- CMOS gate/drain loading: xm1/xm2 ids ~0.1-0.9 uA, xmtail ~1.3-1.6 uA, xm3/xm4
  ~1.5-5.4 uA  (1-2% of the divider currents -> negligible dynamic loading)
- supplies: i(v_vcc_hbt) ~ -135 uA +/- 1.3 uA (essentially constant), i(v_vdd)
  ~ -3.6 uA, i(v_vss) ~ +138 uA

## Classification (PROVISIONAL)
DRIVE/HEADROOM (drive-path level deficiency; NOT dynamic loading; NOT headroom clipping):
1. No headroom loss: ef_p/ef_n swing 0.37-0.92 V with 0.37 V / 1.58 V rail margins;
   no clipping anywhere.
2. No dynamic loading: CMOS gate currents are 1-2% of the divider currents; the
   supply currents are essentially constant across the run; e_cm stays ~0.3 mV.
3. The dominant compression stage is STATIC: gp/ef = 0.395 matches the designed
   divider ratio exactly, and the level shift (VBE ~0.79 V) maps the 1.42 V input
   mid-swing to ~0.63 V at the emitters and ~0.22-0.30 V at the gates - far below
   the 0.6 V rail-midpoint proxy. The gates never enter the CMOS switching region
   (cm_p stays 1.10-1.22 V, cm_n 0.79-0.86 V; inverters never trip; outputs latched).
4. The compression is identical at all 10 crossings (gp/gn alternate ~0.218/0.296 V;
   gate differential ~ +/-0.078 V; outputs never cross 0.6 V).

Interpretation remains UNPROVEN pending PE review; no causality claim beyond the
measured levels/currents; no redesign; no second run.
