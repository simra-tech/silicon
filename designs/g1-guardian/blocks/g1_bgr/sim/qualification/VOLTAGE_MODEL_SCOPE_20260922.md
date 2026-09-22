# Voltage and model scope audit

The existing transient and DC completion results do **not** establish device
reliability. The pinned process document and simulator SOA parameters describe
different limits. No model card, rule deck, nominal circuit or operating rail
has been changed by this audit.

The primary document is the pinned PDK's
`libs.doc/doc/SG13G2_os_process_spec.pdf`, revision1.2, SHA-256
`974d505886ee62932a50c52c22fbc290db4a70d8a7ce129c0ca8d7934aee160e`.
Page4 describes the thick-oxide module for a3.3V supply. Page9 states maximum
gate-source voltage3.3V at27°C for HV NMOS gate length at least0.6µm and HV
PMOS gate length at least0.5µm. This statement does not establish a general
3.6V gate rating or the same rating at every temperature. Breakdown voltages
listed elsewhere in the tables are not operating ratings.

The pinned PSP HV model defaults `SWSOA=0`; its parameter file instead lists
`VGS_MAX`, `VGD_MAX`, `VGB_MAX`, `VDS_MAX` as3.0V and `VDB_MAX`, `VSB_MAX`
as1.6V. A literal comparison against those fields is a diagnostic, not a
resolution of the documentary discrepancy. LV model MAX fields are1.6V.
The HBT header separately specifies maximum collector-emitter voltage1.6V.

`voltage_scope_audit_20260922.json` records source hashes and every baseline
BGR/T2F/OSC MOS geometry. Four BGR and21 T2F HV NMOS instances have0.5µm
gate length, shorter than the page9 condition for3.3V gate bias. Their actual
terminal voltages must be checked; this does not declare every shorter device
invalid at a lower actual gate bias. OSC uses LV devices.

`run_terminal_audit.py` repeats retained BGR fixtures with additional external
terminal export and requires the original saved vectors to remain byte
identical. The81 DC and6 startup repeats now complete with byte-identical original
vectors. All87 contain at least one literal PSP MAX exceedance. Maximum
DC gate-source magnitude is3.6V at XM28; maximum HBT collector-emitter
magnitude is0.858884V for DC and0.784589V for startup. Detailed comparison
with documentary voltage/length/temperature scope remains incomplete. Intrinsic model nodes, every assembled load,
temperature-dependent reliability and lifetime are outside that export.

`model_warning_audit_20260922.json` inventories original warnings without
changing recorded completion or TC outcomes. Temperature-limiter NaN messages
occur in all100 MC and81 DC corner cases; resistor `vmax` warnings occur in
42/100 and27/81 respectively. Their final saved vectors are finite. The six
startup cases contain neither category. Pinned `r3_cmc-patched.va` defaults
`vmax` to9.9e9V and the installed resistor cards do not override it, so these
warnings are not evidence of a low-voltage resistor operating-rating failure.
They concern internal model/control-node quantities, potentially during solver
trial states. Exact intrinsic-node and time attribution remains **not run**.
