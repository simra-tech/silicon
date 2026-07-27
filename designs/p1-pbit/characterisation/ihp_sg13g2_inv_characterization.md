# IHP SG13G2 CMOS Inverter Switching Threshold Characterization Record

## Overview & Context
This characterization evaluates the CMOS inverter switching threshold ($V_{th}$, defined where $V_{out} = V_{DD}/2$) on the IHP SG13G2 130 nm process using `xschem`, `ngspice`, and `CACE`.

Simulations were performed across two complementary 9-cell characterization sweeps from `$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/models/cornerMOSlv.lib`:
1. **Process-by-Supply Matrix at $27^\circ\text{C}$:** Process corners (`mos_ss`, `mos_tt`, `mos_ff`) $\times$ Core supply voltages ($V_{DD} \in \{1.08\,\text{V}, 1.20\,\text{V}, 1.32\,\text{V}\}$).
2. **Process-by-Temperature Matrix at $V_{DD} = 1.20\,\text{V}$:** Process corners (`mos_ss`, `mos_tt`, `mos_ff`) $\times$ Ambient temperatures ($T \in \{-40^\circ\text{C}, 27^\circ\text{C}, 125^\circ\text{C}\}$).

Two device sizing candidates were evaluated:
1. **Unbalanced Baseline Sizing ($W_p = 2.000\,\mu\text{m}$):** $W_p = 2.000\,\mu\text{m}$, $W_n = 1.000\,\mu\text{m}$, $L = 0.130\,\mu\text{m}$.
2. **Balanced Nulled Sizing ($W_p = 1.414\,\mu\text{m}$):** $W_p = 1.414\,\mu\text{m}$, $W_n = 1.000\,\mu\text{m}$, $L = 0.130\,\mu\text{m}$ (chosen to null nominal offset at `mos_tt`, $V_{DD}=1.20\,\text{V}$, $T=27^\circ\text{C}$).

---

## 1. Process-by-Supply Characterization Matrices (at $T = 27^\circ\text{C}$)

### Table 1: Baseline Sizing ($W_p = 2.000\,\mu\text{m}$, $W_n = 1.000\,\mu\text{m}$, $L = 0.130\,\mu\text{m}$)

| Process Corner | Supply ($V_{DD}$) | Target Output ($V_{DD}/2$) | Measured $V_{th}$ | Offset ($\Delta V_{th} = V_{th} - V_{DD}/2$) |
| :---: | :---: | :---: | :---: | :---: |
| **`mos_ss`** | 1.08 V | 0.540000 V | 0.549454 V | **$+9.454\text{ mV}$** |
| **`mos_ss`** | 1.20 V | 0.600000 V | 0.610938 V | **$+10.938\text{ mV}$** |
| **`mos_ss`** | 1.32 V | 0.660000 V | 0.671291 V | **$+11.291\text{ mV}$** |
| **`mos_tt`** | 1.08 V | 0.540000 V | 0.557691 V | **$+17.691\text{ mV}$** |
| **`mos_tt`** | 1.20 V | 0.600000 V | 0.618312 V | **$+18.312\text{ mV}$** |
| **`mos_tt`** | 1.32 V | 0.660000 V | 0.677914 V | **$+17.914\text{ mV}$** |
| **`mos_ff`** | 1.08 V | 0.540000 V | 0.562267 V | **$+22.267\text{ mV}$** |
| **`mos_ff`** | 1.20 V | 0.600000 V | 0.622110 V | **$+22.110\text{ mV}$** |
| **`mos_ff`** | 1.32 V | 0.660000 V | 0.681445 V | **$+21.445\text{ mV}$** |

---

### Table 2: Nulled Sizing ($W_p = 1.414\,\mu\text{m}$, $W_n = 1.000\,\mu\text{m}$, $L = 0.130\,\mu\text{m}$)

| Process Corner | Supply ($V_{DD}$) | Target Output ($V_{DD}/2$) | Measured $V_{th}$ | Offset ($\Delta V_{th} = V_{th} - V_{DD}/2$) |
| :---: | :---: | :---: | :---: | :---: |
| **`mos_ss`** | 1.08 V | 0.540000 V | 0.538715 V | **$-1.285\text{ mV}$** |
| **`mos_ss`** | 1.20 V | 0.600000 V | 0.596689 V | **$-3.311\text{ mV}$** |
| **`mos_ss`** | 1.32 V | 0.660000 V | 0.653153 V | **$-6.847\text{ mV}$** |
| **`mos_tt`** | 1.08 V | 0.540000 V | 0.543171 V | **$+3.171\text{ mV}$** |
| **`mos_tt`** | 1.20 V | 0.600000 V | 0.600017 V | **$+0.017\text{ mV}$** |
| **`mos_tt`** | 1.32 V | 0.660000 V | 0.655501 V | **$-4.499\text{ mV}$** |
| **`mos_ff`** | 1.08 V | 0.540000 V | 0.544437 V | **$+4.437\text{ mV}$** |
| **`mos_ff`** | 1.20 V | 0.600000 V | 0.600257 V | **$+0.257\text{ mV}$** |
| **`mos_ff`** | 1.32 V | 0.660000 V | 0.655232 V | **$-4.768\text{ mV}$** |

---

### Process-by-Supply Sensitivity & Spread Analysis

#### 1. Process Spread per Supply ($\max(V_{th}) - \min(V_{th})$ across corners)
* **At Low Supply ($V_{DD} = 1.08\,\text{V}$):**
  * Baseline ($2.000\,\mu\text{m}$): $0.562267 - 0.549454 = \mathbf{12.813\text{ mV}}$
  * Nulled ($1.414\,\mu\text{m}$): $0.544437 - 0.538715 = \mathbf{5.722\text{ mV}}$ (shrank by $55.3\%$)
* **At Nominal Supply ($V_{DD} = 1.20\,\text{V}$):**
  * Baseline ($2.000\,\mu\text{m}$): $0.622110 - 0.610938 = \mathbf{11.172\text{ mV}}$
  * Nulled ($1.414\,\mu\text{m}$): $0.600257 - 0.596689 = \mathbf{3.568\text{ mV}}$ (shrank by $68.1\%$)
* **At High Supply ($V_{DD} = 1.32\,\text{V}$):**
  * Baseline ($2.000\,\mu\text{m}$): $0.681445 - 0.671291 = \mathbf{10.154\text{ mV}}$
  * Nulled ($1.414\,\mu\text{m}$): $0.655501 - 0.653153 = \mathbf{2.348\text{ mV}}$ (shrank by $76.9\%$)

*Note on Process Corner Ordering Inversion:* At $V_{DD} = 1.32\,\text{V}$ under nulled sizing, process corner ordering inverts: `mos_tt` ($-4.499\text{ mV}$) sits above `mos_ff` ($-4.768\text{ mV}$), so the upper boundary of the process spread at high supply is defined by typical rather than fast.

#### 2. Peak Absolute Offset Figure
* **Baseline Sizing ($2.000\,\mu\text{m}$):** **$+22.267\text{ mV}$** (located at `mos_ff`, $V_{DD} = 1.08\,\text{V}$).
* **Nulled Sizing ($1.414\,\mu\text{m}$):** **$-6.847\text{ mV}$** ($\approx \mathbf{6.85\text{ mV}}$, located at `mos_ss`, $V_{DD} = 1.32\,\text{V}$).
* **Improvement:** Peak worst-case offset anywhere in the process-by-supply matrix dropped from **$22.27\text{ mV}$** to **$6.85\text{ mV}$**.

#### 3. Total Envelope Figure Across All 9 Process-by-Supply Conditions
* **Baseline Sizing ($2.000\,\mu\text{m}$):**
  * Maximum offset: $+22.267\text{ mV}$ (`mos_ff`, $1.08\text{ V}$)
  * Minimum offset: $+9.454\text{ mV}$ (`mos_ss`, $1.08\text{ V}$)
  * Total Envelope: $22.267 - 9.454 = \mathbf{12.813\text{ mV}}$ ($\approx \mathbf{12.8\text{ mV}}$).
* **Nulled Sizing ($1.414\,\mu\text{m}$):**
  * Maximum offset: $+4.437\text{ mV}$ (`mos_ff`, $1.08\text{ V}$)
  * Minimum offset: $-6.847\text{ mV}$ (`mos_ss`, $1.32\text{ V}$)
  * Total Envelope: $+4.437 - (-6.847) = \mathbf{11.284\text{ mV}}$ ($\approx \mathbf{11.3\text{ mV}}$).

---

## 2. Process-by-Temperature Characterization Matrix (at $V_{DD} = 1.20\,\text{V}$, $W_p = 1.414\,\mu\text{m}$)

### Table 3: Process $\times$ Temperature Matrix ($V_{DD} = 1.20\,\text{V}$, $W_p = 1.414\,\mu\text{m}$, $W_n = 1.000\,\mu\text{m}$, $L = 0.130\,\mu\text{m}$)

| Process Corner | Temperature | Target Output ($V_{DD}/2$) | Measured $V_{th}$ | Offset ($\Delta V_{th} = V_{th} - V_{DD}/2$) |
| :---: | :---: | :---: | :---: | :---: |
| **`mos_ss`** | $-40^\circ\text{C}$ | 0.600000 V | 0.599501 V | **$-0.499\text{ mV}$** |
| **`mos_ss`** | $+27^\circ\text{C}$ | 0.600000 V | 0.596689 V | **$-3.311\text{ mV}$** |
| **`mos_ss`** | $+125^\circ\text{C}$ | 0.600000 V | 0.595450 V | **$-4.550\text{ mV}$** |
| **`mos_tt`** | $-40^\circ\text{C}$ | 0.600000 V | 0.605173 V | **$+5.173\text{ mV}$** |
| **`mos_tt`** | $+27^\circ\text{C}$ | 0.600000 V | 0.600017 V | **$+0.017\text{ mV}$** |
| **`mos_tt`** | $+125^\circ\text{C}$ | 0.600000 V | 0.598398 V | **$-1.602\text{ mV}$** |
| **`mos_ff`** | $-40^\circ\text{C}$ | 0.600000 V | 0.605708 V | **$+5.708\text{ mV}$** |
| **`mos_ff`** | $+27^\circ\text{C}$ | 0.600000 V | 0.600257 V | **$+0.257\text{ mV}$** |
| **`mos_ff`** | $+125^\circ\text{C}$ | 0.600000 V | 0.600681 V | **$+0.681\text{ mV}$** |

---

## Process vs. Temperature Sensitivity Analysis

### 1. Dominant Temperature Axis at Nominal Supply
Under nominal supply voltage ($V_{DD} = 1.20\,\text{V}$), **temperature is the dominant sensitivity axis**:
* Temperature variation moves the switching threshold offset **about twice as much as process corner variation does**:
  * **Temperature Spread (`mos_tt` across $-40^\circ\text{C} \to +125^\circ\text{C}$):** **$6.775\text{ mV}$** ($+5.173\text{ mV}$ down to $-1.602\text{ mV}$).
  * **Process Spread ($27^\circ\text{C}$ across `mos_ss` $\to$ `mos_ff`):** **$3.568\text{ mV}$** ($-3.311\text{ mV}$ up to $+0.257\text{ mV}$).

### 2. Point Trim vs. Global Null
* **The $W_p = 1.414\,\mu\text{m}$ null is strictly a $27^\circ\text{C}$ point trim rather than a global null**:
  * While $W_p = 1.414\,\mu\text{m}$ achieves an excellent near-zero offset of **$+17\,\mu\text{V}$** ($+0.017\text{ mV}$) at room temperature ($27^\circ\text{C}$), that same sizing drifts to **$+5.173\text{ mV}$** at $-40^\circ\text{C}$ and **$-1.602\text{ mV}$** at $+125^\circ\text{C}$ in the typical corner.
  * Static transistor width tuning nulls offset at a single operating point, but does not cancel temperature-dependent mobility and threshold voltage drift ($V_{th0}(T)$).

### 3. Combined Process-by-Temperature Envelope
* **Maximum Offset:** $+5.708\text{ mV}$ (`mos_ff`, $-40^\circ\text{C}$)
* **Minimum Offset:** $-4.550\text{ mV}$ (`mos_ss`, $+125^\circ\text{C}$)
* **Total Envelope Across Process $\times$ Temp:** $5.708 - (-4.550) = \mathbf{10.258\text{ mV}}$.

---

## Design Trade-off Summary

1. **Better Absolute Offset:** Nulling $W_p$ to $1.414\,\mu\text{m}$ eliminates the $+18.3\text{ mV}$ systematic DC offset at nominal conditions ($0.600017\text{ V}$ vs. $0.600000\text{ V}$ target) and reduces the worst-case matrix offset from $22.3\text{ mV}$ to $6.9\text{ mV}$.
2. **Process Sensitivity Reduction:** The true process spread ($\max - \min$ across corners) narrowed significantly from $11.2\text{ mV}$ down to $3.6\text{ mV}$ at nominal supply, from $12.8\text{ mV}$ down to $5.7\text{ mV}$ at low supply, and from $10.2\text{ mV}$ down to $2.3\text{ mV}$ ($2.348\text{ mV}$, $76.9\%$ reduction) at high supply.
3. **Supply Sensitivity Rotation:** While the baseline $2.0\,\mu\text{m}$ sizing exhibited flat offsets across supply ($+17.7\text{ mV} \dots +18.3\text{ mV}$ spread $<0.6\text{ mV}$), the $1.414\,\mu\text{m}$ sizing introduced a supply tilt ($+3.17\text{ mV}$ at $1.08\text{ V}$ down to $-4.50\text{ mV}$ at $1.32\text{ V}$, a $7.67\text{ mV}$ supply spread).
4. **Overall Variation Envelope:** Across the complete 9-cell process-by-supply space at $27^\circ\text{C}$, the total variation envelope changed only marginally (dropping from **$12.8\text{ mV}$** to **$11.3\text{ mV}$**). The process and supply sensitivities effectively swapped roles.
