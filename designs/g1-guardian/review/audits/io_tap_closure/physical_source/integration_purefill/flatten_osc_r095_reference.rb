# Comparison-only OSC R0.95 source representation: reuse the frozen RZ100
# stock-reader/writer flatten proof with only its pinned input hash updated.
require 'digest'
base = File.join(File.dirname(__FILE__), 'flatten_rz_reference.rb')
raise 'frozen flatten proof changed' unless Digest::SHA256.file(base).hexdigest ==
  'a28dcbcd6edfb3e03ebf73fd16f629c4bb0745359964b2344eb5849a224b8525'
old_sha = '9f38371f303672a7169733493c9d444cacbda2d5889e0f79659b5e1224490369'
new_sha = '5e280d2e5e6955435e789a9838331d40eec83f9b1566e51d2a0796be06489dad'
body = File.read(base)
raise 'expected exactly one source hash substitution' unless body.scan(old_sha).size == 1
raise 'comparison source not provided' unless $source && Digest::SHA256.file($source).hexdigest == new_sha
eval(body.sub(old_sha, new_sha), TOPLEVEL_BINDING, base)
