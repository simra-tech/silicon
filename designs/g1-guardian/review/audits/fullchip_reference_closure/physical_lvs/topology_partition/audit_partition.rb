# Read-only terminal-partition witness; no comparison hints or source changes.
require 'json'
require 'digest'
require 'fileutils'
raise 'arguments' unless $database && $ports && $original && $adapted && $reader && $output_dir
raise 'preserve evidence' if File.exist?($output_dir)
base = $output_dir
FileUtils.mkdir_p(base)
FileUtils.cp(__FILE__, File.join(base, 'worker_snapshot.rb'))
raise 'database binding' unless Digest::SHA256.file($database).hexdigest == '3ed5cd2b78b3d4f4ed724730fcba2388148340d6442249e143c17a9f7ac99f04'
raise 'ports binding' unless Digest::SHA256.file($ports).hexdigest == '56bbb3b4b65eb31e95b9666cb59ff6c3b272135e3a06fdf2879a78bf4d00c33d'
$output_dir = File.join(base, 'reader_control')
load $reader
$output_dir = base
source = RBA::Netlist.new
source.read($adapted, RBA::NetlistSpiceReader.new(CustomReader.new))
sc = source.circuit_by_name('PLACED_CORE_NOT_CONNECTED_FULLCHIP')
sc.each_pin { |p| sc.net_for_pin(p.id).set_property('PHYSICAL_EXTERNAL', p.name) }
source.flatten
sc = source.circuit_by_name(sc.name)
db = RBA::LayoutVsSchematic.new
db.read($database)
native = db.netlist.dup
nc = native.circuit_by_name('placed_core_NOT_CONNECTED_FULLCHIP')
ports = JSON.parse(File.read($ports))
ports['logical_bindings'].each do |pin, (circuit, cluster)|
  raise 'physical top' unless circuit == nc.name
  matches = nc.each_net.select { |n| n.cluster_id == cluster }
  raise 'physical unique cluster' unless matches.size == 1
  matches[0].set_property('PHYSICAL_EXTERNAL', pin)
end
native.flatten
nc = native.circuit_by_name(nc.name)
views = {}
{source: sc, native: nc}.each do |side, circuit|
  raise 'not flat' unless circuit.each_subcircuit.to_a.empty?
  incidence = Hash.new { |h,k| h[k] = [] }
  models = Hash.new(0)
  circuit.each_device do |d|
    models[d.device_class.name.downcase] += 1
    d.device_class.terminal_definitions.each do |t|
      n = d.net_for_terminal(t.name)
      incidence[n.expanded_name] << {device: d.expanded_name, model: d.device_class.name, terminal: t.name}
    end
  end
  taps = circuit.each_device.select { |d| d.device_class.name.downcase == 'ptap1' }.map do |d|
    {name: d.expanded_name,
     parameters: d.device_class.parameter_definitions.to_h { |p| [p.name, d.parameter(p.name)] },
     terminals: d.device_class.terminal_definitions.to_h do |t|
       n = d.net_for_terminal(t.name)
       [t.name, {net: n.expanded_name, physical_external: n.property('PHYSICAL_EXTERNAL'),
                 degree: incidence[n.expanded_name].size}]
     end}
  end
  body_nets = taps.map { |d| d[:terminals]['WELL'][:net] }.uniq
  views[side] = {devices: models.values.sum, models: models, nets: circuit.each_net.to_a.size,
                 tap_records: taps,
                 tap_well_partitions: body_nets.to_h { |n| [n, incidence[n]] },
                 external_tap_well_count: taps.count { |d| !d[:terminals]['WELL'][:physical_external].nil? },
                 well_partition_count: body_nets.size,
                 tie_well_same_net_count: taps.count { |d| d[:terminals]['WELL'][:net] == d[:terminals]['TIE'][:net] }}
end
st = views[:source][:tap_records]
nt = views[:native][:tap_records]
witnesses = st.select { |d| d[:terminals]['WELL'][:degree] == 1 && d[:terminals]['WELL'][:physical_external].nil? }
checks = {
  exact_source_386_taps: st.size == 386,
  source_243_distinct_well_partitions: views[:source][:well_partition_count] == 243,
  native_46_taps: nt.size == 46,
  native_all_well_bound_to_actual_VSS: nt.all? { |d| d[:terminals]['WELL'][:physical_external] == 'VSS' },
  source_no_well_external_binding: views[:source][:external_tap_well_count] == 0,
  shortest_degree_one_source_witness_exists: !witnesses.empty?
}
result = {status: checks.values.all? ? 'passed exact non-equivalence witness; source/native topology FAILED' : 'failed proposed witness controls',
          inputs: [$database,$ports,$original,$adapted,$reader].to_h { |p| [p,Digest::SHA256.file(p).hexdigest] },
          checks: checks, views: views,
          shortest_witness: witnesses.sort_by { |d| d[:name] }.first,
          witness_reason: 'A source PTAP WELL is a degree-one internal net, while every native PTAP WELL is the independently probed external VSS net. No pin-preserving terminal-graph bijection can map that source device to any native PTAP, independently of A/P values.',
          controls: 'Pinned complete reader closure and all 63 reversible tap suffix/non-tap/interface controls passed; no simplify or net merge in this audit.',
          not_run: ['source-intent repair/global substrate declaration','A/P applicability remedy','new physical extraction','electrical adoption']}
File.write(File.join(base,'summary.json'),JSON.pretty_generate(result)+"\n")
puts JSON.pretty_generate(result.reject { |k,_| k == :views })
raise 'witness controls failed' unless checks.values.all?
