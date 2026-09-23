# Direct in-memory diagnostic. No 12-digit SPICE round trip or layout rerun.
require 'json'
require 'digest'
require 'fileutils'
raise 'Required arguments' unless $original && $adapted && $database && $output_dir && $variant
raise 'Unknown variant' unless %w[original adapter].include?($variant)
raise 'Preserve output' if File.exist?($output_dir)
diagnostic_dir = $output_dir
FileUtils.mkdir_p(diagnostic_dir)
FileUtils.cp(__FILE__, File.join(diagnostic_dir, 'worker_snapshot.rb'))
raise 'Saved database changed' unless Digest::SHA256.file($database).hexdigest == '1c8f3f91b8be00e0fbbdf4c2a40734fb5f8fe8b0388b1780768699e1a2afcbcf'
# Reuse the proven, complete pinned class setup and original/adapter reader
# control. This executes no geometry extraction and no model-card changes.
$output_dir = File.join(diagnostic_dir, 'reader_control')
load File.join(File.dirname(__FILE__), 'probe_tap_adapter.rb')
$output_dir = diagnostic_dir
report = {status: 'running native API preparation', variant: $variant,
          comparison_scope: 'Saved parent-connected netlist API diagnostic, NOT new native extraction or adoption',
          database_sha256: Digest::SHA256.file($database).hexdigest,
          source_sha256: Digest::SHA256.file($variant == 'original' ? $original : $adapted).hexdigest,
          independent_flatten_proof: 'Required externally before launch; original hierarchy terminal unions and binary64 parameters'}
save = lambda { File.write(File.join(diagnostic_dir, 'summary.json'), JSON.pretty_generate(report) + "\n") }
save.call
# Positive and wrong-wire/parameter/pin controls for this exact API route.
toy = lambda do |change|
  nl = RBA::Netlist.new
  klass = RBA::DeviceClassResistor.new
  klass.name = 'CONTROL_R'
  nl.add(klass)
  c = RBA::Circuit.new
  c.name = 'CONTROL_TOP'
  nl.add(c)
  n = %w[A X B].to_h { |name| [name, c.create_net(name)] }
  %w[A B].each do |name|
    next if change == 'pin' && name == 'B'
    pin = c.create_pin(name)
    c.connect_pin(pin.id, n.fetch(name))
  end
  [['RA', 'A', 'X', 1000.0], ['RB', change == 'wire' ? 'A' : 'X', 'B', change == 'parameter' ? 2100.0 : 2000.0]].each do |name, a, b, r|
    d = c.create_device(klass, name)
    d.connect_terminal('A', n.fetch(a))
    d.connect_terminal('B', n.fetch(b))
    d.set_parameter('R', r)
  end
  [nl, c]
end
report[:API_controls] = []
%w[none wire parameter pin].each do |change|
  na, ca = toy.call('none')
  nb, cb = toy.call(change)
  xr = RBA::NetlistCrossReference.new
  matched = RBA::NetlistComparer.new.compare(ca, cb, xr)
  strict = matched && ca.each_pin.map(&:name).sort == cb.each_pin.map(&:name).sort
  xr.each_circuit_pair do |pair|
    strict &&= pair.status == RBA::NetlistCrossReference::Match
    %i[each_device_pair each_net_pair each_pin_pair each_subcircuit_pair].each do |method|
      xr.send(method, pair) { |p| strict &&= p.status == RBA::NetlistCrossReference::Match }
    end
  end
  raise "API negative control failed: #{change}" unless strict == (change == 'none')
  report[:API_controls] << {case: change, engine_equivalent: matched, strict: strict, status: 'passed expected disposition'}
end
save.call
db = RBA::LayoutVsSchematic.new
db.read($database)
native = db.netlist.dup
native.each_circuit do |circuit|
  [circuit.each_device.to_a, circuit.each_subcircuit.to_a].flatten.each do |obj|
    obj.name = obj.expanded_name if obj.name.empty?
  end
end
native.flatten
old = native.circuit_by_name('placed_core_NOT_CONNECTED_FULLCHIP')
raise 'Native top missing' unless old
raise 'Flatten incomplete' unless old.each_subcircuit.to_a.empty?
layout = RBA::Netlist.new
layout.case_sensitive = native.is_case_sensitive?
lc = RBA::Circuit.new
lc.name = old.name
layout.add(lc)
reader = CustomReader.new
classes = {}
class_rows = []
used_models = old.each_device.map { |d| d.device_class.name }.uniq
native.each_device_class do |klass|
  next unless used_models.include?(klass.name)
  keys = PREFIX_MAP.keys.select { |key| key.downcase == klass.name.downcase }
  raise "Unknown/ambiguous model prefix #{klass.name}" unless keys.size == 1
  prefix = PREFIX_MAP[keys[0]]
  fresh = reader.send(:create_device_class, prefix, lc, klass.name, klass.terminal_definitions.size)
  raise 'Parameter schema changed' unless klass.parameter_definitions.map(&:name) == fresh.parameter_definitions.map(&:name)
  raise 'Terminal schema changed' unless klass.terminal_definitions.map(&:name) == fresh.terminal_definitions.map(&:name)
  classes[klass.name] = fresh
  class_rows << {model: klass.name, prefix: prefix, saved_type: klass.class.name,
                 installed_constructor_type: fresh.class.name,
                 parameters: fresh.parameter_definitions.map(&:name), terminals: fresh.terminal_definitions.map(&:name)}
end
nets = {}
old.each_net.with_index do |net, index|
  net.set_property('G1_DIAGNOSTIC_NET_ID', index)
  nets[index] = lc.create_net(net.name)
  nets[index].set_property('G1_DIAGNOSTIC_NET_ID', index)
end
raise 'Net cloning merged distinct conductors' unless lc.each_net.to_a.size == nets.size
raise 'Net identity collision' unless nets.all? { |index, net| net.property('G1_DIAGNOSTIC_NET_ID') == index }
count, terminals, parameter_count = 0, 0, 0
old.each_device do |dev|
  fresh = lc.create_device(classes.fetch(dev.device_class.name), dev.expanded_name)
  dev.device_class.parameter_definitions.each do |param|
    v = dev.parameter(param.name)
    fresh.set_parameter(param.name, v)
    raise 'Binary64 parameter changed' unless [fresh.parameter(param.name)].pack('G') == [v].pack('G')
    parameter_count += 1
  end
  dev.device_class.terminal_definitions.each do |terminal|
    net_id = dev.net_for_terminal(terminal.name).property('G1_DIAGNOSTIC_NET_ID')
    fresh.connect_terminal(terminal.name, nets.fetch(net_id))
    raise 'Terminal clone changed' unless fresh.net_for_terminal(terminal.name) == nets.fetch(net_id)
    raise 'Terminal net identity changed' unless fresh.net_for_terminal(terminal.name).property('G1_DIAGNOSTIC_NET_ID') == net_id
    terminals += 1
  end
  count += 1
end
old.each_pin do |pin|
  new_pin = lc.create_pin(pin.name)
  lc.connect_pin(new_pin.id, nets.fetch(old.net_for_pin(pin.id).property('G1_DIAGNOSTIC_NET_ID')))
end
raise 'Primitive count changed' unless count == 61_516 && lc.each_device.to_a.size == count
raise 'Original 71 pins changed' unless lc.each_pin.map(&:name) == old.each_pin.map(&:name) && lc.each_pin.to_a.size == 71
reference = RBA::Netlist.new
reference.read($variant == 'original' ? $original : $adapted, RBA::NetlistSpiceReader.new(CustomReader.new))
reference.flatten
rc = reference.circuit_by_name('PLACED_CORE_NOT_CONNECTED_FULLCHIP')
raise 'Source top missing' unless rc && rc.each_pin.to_a.size == 22
inventory = lambda do |circuit|
  {devices: circuit.each_device.to_a.size, nets: circuit.each_net.to_a.size,
   pins: circuit.each_pin.map(&:name), models: circuit.each_device.group_by { |d| d.device_class.name }.transform_values(&:size)}
end
report[:before_simplify] = {layout: inventory.call(lc), reference: inventory.call(rc)}
report[:class_factory_projection] = class_rows
report[:clone_checks] = {all_61516_primitive_records: 'passed', binary64_parameters: parameter_count,
                         actual_terminal_bindings: terminals, full_native_pin_inventory: 'passed 71 unchanged',
                         geometry_or_source_model_edits: 'not applicable'}
save.call
# Same simplification routine and unchanged stock constructors/combiners.
layout.simplify
reference.simplify
report[:after_simplify] = {layout: inventory.call(lc), reference: inventory.call(rc)}
comparer = RBA::NetlistComparer.new
comparer.max_resistance = 1e9
comparer.min_capacitance = 1e-18
# Only uniquely identical model spellings modulo SPICE case are bound.
bindings = []
layout.each_device_class do |klass|
  matches = reference.each_device_class.select { |c| c.name.downcase == klass.name.downcase }
  raise 'Ambiguous source class case binding' if matches.size > 1
  next if matches.empty?
  other = matches[0]
  raise 'Case-bound terminal schema differs' unless klass.terminal_definitions.map { |t| t.name.downcase } == other.terminal_definitions.map { |t| t.name.downcase }
  raise 'Case-bound parameter schema differs' unless klass.parameter_definitions.map(&:name) == other.parameter_definitions.map(&:name)
  comparer.same_device_classes(klass, other)
  bindings << [klass.name, other.name]
end
report[:case_only_class_bindings] = bindings
report[:comparer] = {max_resistance: 1e9, min_capacitance: 1e-18,
                     implicit_net_joins: false, same_net_hints: false, parameter_tolerance_changes: false,
                     top_pin_edits: false, custom_constructors: 'Exact installed source-reader factories'}
report[:status] = 'running bounded API comparison'
save.call
xref = RBA::NetlistCrossReference.new
matched = comparer.compare(lc, rc, xref)
statuses = {RBA::NetlistCrossReference::Match => 'Match', RBA::NetlistCrossReference::MatchWithWarning => 'MatchWithWarning',
            RBA::NetlistCrossReference::Mismatch => 'Mismatch', RBA::NetlistCrossReference::NoMatch => 'NoMatch',
            RBA::NetlistCrossReference::Skipped => 'Skipped', RBA::NetlistCrossReference::None => 'None'}
describe = lambda do |dev|
  next nil unless dev
  {name: dev.expanded_name, model: dev.device_class.name,
   parameters: dev.device_class.parameter_definitions.to_h { |p| [p.name, dev.parameter(p.name)] },
   terminals: dev.device_class.terminal_definitions.to_h { |t| [t.name, dev.net_for_terminal(t.name)&.expanded_name] }}
end
rows = []
xref.each_circuit_pair do |pair|
  row = {layout: pair.first&.name, reference: pair.second&.name, status: statuses.fetch(pair.status), pairs: {}, bad: {}}
  {device: :each_device_pair, net: :each_net_pair, pin: :each_pin_pair, subcircuit: :each_subcircuit_pair}.each do |kind, method|
    counts, bad = Hash.new(0), []
    xref.send(method, pair) do |p|
      status = statuses.fetch(p.status)
      counts[status] += 1
      next if status == 'Match'
      conv = kind == :device ? describe : lambda { |obj| obj&.name }
      bad << {status: status, layout: conv.call(p.first), reference: conv.call(p.second)}
    end
    row[:pairs][kind], row[:bad][kind] = counts, bad
  end
  rows << row
end
File.write(File.join(diagnostic_dir, 'comparison.json'), JSON.pretty_generate(rows) + "\n")
report[:engine_equivalent] = matched
report[:strict_source_top_pin_set] = lc.each_pin.map(&:name).sort == rc.each_pin.map(&:name).sort
report[:all_pairs_strict_Match] = !rows.empty? && rows.all? { |r| r[:status] == 'Match' && r[:pairs].values.all? { |c| (c.keys - ['Match']).empty? } }
report[:status] = matched && report[:strict_source_top_pin_set] && report[:all_pairs_strict_Match] ? 'passed scoped API comparison only' : 'failed scoped API comparison'
report[:new_native_extraction] = 'not run'
report[:physical_adoption] = 'not run'
save.call
puts JSON.pretty_generate(report.reject { |k, _| k == :class_factory_projection })
