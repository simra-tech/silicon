# Comparison-only adaptation of the unchanged qualified stock reader roundtrip.
require 'digest'
require 'json'
base = File.join(File.dirname(__FILE__), '../../../../../..', 'designs/g1-guardian/review/audits/io_tap_closure/physical_source/integration_purefill/flatten_rz_reference.rb')
raise 'base changed' unless Digest::SHA256.file(base).hexdigest == 'a28dcbcd6edfb3e03ebf73fd16f629c4bb0745359964b2344eb5849a224b8525'
raise 'args' unless $source && $projection_proof && $output_dir
proof = JSON.parse(File.read($projection_proof))
raise 'projection not proved' unless proof['status'] == 'passed reversible source-only comparison projection; physical audit separate' && proof['reverse_bytes_exact'] && proof['only_two_soft_size_lines_changed']
expected = proof.fetch('projected_source_sha256')
raise 'source changed' unless Digest::SHA256.file($source).hexdigest == expected
body=File.read(base)
original='9f38371f303672a7169733493c9d444cacbda2d5889e0f79659b5e1224490369'
raise 'one binding required' unless body.scan(original).size==1
eval(body.sub(original,expected),TOPLEVEL_BINDING,base)
