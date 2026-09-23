# Frozen comparison-only source, stock PDK reader/writer, no electrical edits.
require 'json'
require 'digest'
require 'logger'
require 'fileutils'
raise 'arguments' unless $source && $output_dir
raise 'preserve outputs' if File.exist?($output_dir)
source_sha = '9f38371f303672a7169733493c9d444cacbda2d5889e0f79659b5e1224490369'
raise 'source changed' unless Digest::SHA256.file($source).hexdigest == source_sha
pdk = '/foss/pdks/ihp-sg13g2'
raise 'PDK changed' unless File.read(File.join(pdk, 'COMMIT')).strip == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
def logger; @rz_logger ||= Logger.new($stdout); end
def dbu; 0.001; end
SERIES_RES = true
PARALLEL_RES = true
rules = File.join(pdk, 'libs.tech/klayout/tech/lvs/rule_decks')
files = %w[globals.lvs custom_reader.lvs custom_writer.lvs custom_devices.lvs
           custom_combiner.lvs custom_extractor.lvs custom_mim_extractor.lvs
           custom_bjt_extractor.lvs custom_isolbox_extractor.lvs]
files.each { |name| load File.join(rules, name) }
reader = RBA::NetlistSpiceReader.new(CustomReader.new)
original = RBA::Netlist.new
original.read($source, reader)
top_name = 'PLACED_CORE_NOT_CONNECTED_FULLCHIP'
top = original.circuit_by_name(top_name)
raise 'top missing' unless top && top.each_pin.to_a.size == 22
reachable = []
pending = [top]
until pending.empty?
  cell = pending.pop
  next if reachable.include?(cell.name)
  reachable << cell.name
  cell.each_subcircuit { |inst| pending << inst.circuit_ref }
end
flat = original.dup
flat.flatten
ft = flat.circuit_by_name(top_name)
raise 'flat top invalid' unless ft && ft.each_pin.to_a.size == 22 && ft.each_subcircuit.to_a.empty?
unused = flat.each_circuit.reject { |c| c.name == top_name }
raise 'reachable definition survived' unless unused.none? { |c| reachable.include?(c.name) }
unused_names = unused.map(&:name)
unused.each { |c| flat.remove(c) }
raise 'source scope changed' unless flat.each_circuit.map(&:name) == [top_name]
raise 'primitive count wrong' unless ft.each_device.to_a.size == 76059
FileUtils.mkdir_p($output_dir)
dest = File.join($output_dir, 'physical_AP_three_dummy_flat_reference.cdl')
writer = RBA::NetlistSpiceWriter.new(CustomWriter.new)
writer.use_net_names = true
writer.with_comments = true
flat.write(dest, writer)
# The stock writer emits numeric-leading instance names for these seven
# custom classes; the stock reader ignores such lines. Prefix only the SPICE
# type letter selected from the immediately preceding pinned class comment.
prefix = {'CAP_CMIM'=>'C','DANTENNA'=>'D','DPANTENNA'=>'D','NPN13G2'=>'Q',
          'PTAP1'=>'R','RHIGH'=>'R','RPPD'=>'R'}
lines = File.readlines(dest)
model = nil
fixed = Hash.new(0)
lines.map! do |line|
  model = Regexp.last_match(1).strip if line =~ /^\* device instance .* (\S+)\s*$/
  if line =~ /^\d/
    raise "unexpected custom class #{model}" unless prefix.key?(model)
    fixed[model] += 1
    prefix.fetch(model) + line
  else
    line
  end
end
raise 'custom writer count changed' unless fixed.values.sum == 2522
File.write(dest, lines.join)
round = RBA::Netlist.new
round.read(dest, RBA::NetlistSpiceReader.new(CustomReader.new))
rt = round.circuit_by_name(top_name)
raise 'roundtrip interface/primitive changed' unless rt && rt.each_pin.map(&:name) == ft.each_pin.map(&:name) &&
  rt.each_device.to_a.size == ft.each_device.to_a.size && rt.each_subcircuit.to_a.empty?
xref = RBA::NetlistCrossReference.new
cmp = RBA::NetlistComparer.new
cmp.max_resistance = 1e9
cmp.min_capacitance = 1e-18
match = cmp.compare(flat, round, xref)
pairs = {}
xref.each_circuit_pair do |cp|
  next unless cp.first && cp.first.name == top_name
  pairs[:circuit] = cp.status.to_s
  %i[device net pin subcircuit].each do |kind|
    counts = Hash.new(0)
    xref.send("each_#{kind}_pair", cp) { |p| counts[p.status.to_s] += 1 }
    pairs[kind] = counts
  end
end
strict = match && pairs[:circuit] == RBA::NetlistCrossReference::Match.to_s &&
  %i[device net pin subcircuit].all? { |kind| pairs[kind].keys.all? { |key| key == RBA::NetlistCrossReference::Match.to_s } } &&
  pairs[:device].values.sum == 76059 && pairs[:pin].values.sum == 22
report = {status: strict ? 'passed exact stock-reader source flatten roundtrip' : 'failed stock-reader source flatten roundtrip',
          input_sha256: source_sha, output_sha256: Digest::SHA256.file(dest).hexdigest,
          reachable_definitions: reachable.sort, unused_unreachable_library_roots: unused_names.sort,
          source_top_pins: ft.each_pin.map(&:name), primitive_count: ft.each_device.to_a.size,
          repaired_stock_writer_custom_instance_prefixes: fixed,
          roundtrip_pairs: pairs, deck_model_source_edits: 'not applicable', strict_stock_LVS: 'not run'}
File.write(File.join($output_dir, 'summary.json'), JSON.pretty_generate(report) + "\n")
puts JSON.generate({status: report[:status], output_sha256: report[:output_sha256], roundtrip_pairs: pairs})
raise 'roundtrip mismatch' unless strict
