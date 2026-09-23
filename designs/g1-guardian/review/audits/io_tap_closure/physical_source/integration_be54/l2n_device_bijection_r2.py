#!/usr/bin/env python3
"""Native literal-token binding, then separately exact captured binary64."""
import ctypes
import hashlib
from pathlib import Path

libc=ctypes.CDLL(None)


def native_token(value):
    buffer=ctypes.create_string_buffer(128)
    result=libc.snprintf(buffer,128,b'%.12g',ctypes.c_double(value))
    assert 0<result<128
    return buffer.value.decode('ascii')


base=Path(__file__).resolve().with_name('l2n_device_bijection.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='bb38d69b5210690d29f47f26bb74fc978b53444a69f43b7a7851a6917af638c3'
code=base.read_text()
changes=[
 ("name='',parameters={},terminals={}","name='',parameters={},terminals={},tokens={}"),
 ("device['parameters'][items[0]]=float(items[1])","device['parameters'][items[0]]=float(items[1]);device['tokens'][items[0]]=items[1]"),
 ("assert all(struct.pack('>d',v)==struct.pack('>d',actual['parameters'][p]) for p,v in doc['parameters'].items())",
  "assert all(native_token(actual['parameters'][p])==token for p,token in doc['tokens'].items()),(doc,actual)"),
 ("assert float(format(precise,'.12g'))==doc['parameters'][pn],(old,pn)",
  "assert native_token(precise)==doc['tokens'][pn],(old,pn)"),
 ("all_document_parameter_tokens_and_terminal_net_ids_exact=True,",
  "all_document_parameter_tokens_and_terminal_net_ids_exact=True,\n"
  "        formatter='native C %.12g; v0.30.9 dbLayoutToNetlistWriter.cc line837; actual literal full-domain check',\n"
  "        pre_restoration_binary64_readback='failed retained; never asserted exact',"),
]
for old,new in changes:
    assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
anchor='    assert negative_swap is not None\n'
assert code.count(anchor)==1
addition='''    first_c=next(c for c,rs in docs.items() if rs)
    first_doc=docs[first_c][0];first_actual=actual[first_c][0]
    import copy
    for kind in ('terminal','parameter-token'):
        bad=copy.deepcopy(first_doc)
        if kind=='terminal':
            key=next(iter(bad['terminals']));old_value=bad['terminals'][key]
            bad['terminals'][key]=1 if old_value is None else old_value+1
        else:
            key=next(iter(bad['tokens']));bad['tokens'][key]=native_token(bad['parameters'][key]+1.0)
        rejected=False
        try:check_record(bad,first_actual)
        except AssertionError:rejected=True
        assert rejected,kind
'''
code=code.replace(anchor,anchor+addition)
code=code.replace('negative_missing_and_duplicate_identity_rejected=True,',
    'negative_missing_and_duplicate_identity_rejected=True,negative_terminal_and_parameter_token_rejected=True,')
exec(compile(code,str(base),'exec'),globals())
