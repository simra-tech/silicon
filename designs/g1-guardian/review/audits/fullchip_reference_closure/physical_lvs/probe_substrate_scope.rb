# Read-only pinned-reader scope evidence. Synthetic controls are not a chip fix.
require 'json'
require 'digest'
require 'fileutils'
raise 'arguments' unless $original && $adapted && $database && $output_dir
raise 'preserve outputs' if File.exist?($output_dir)
base = $output_dir
FileUtils.mkdir_p(base)
FileUtils.cp(__FILE__, File.join(base, 'worker_snapshot.rb'))
$output_dir = File.join(base, 'reader_control')
load File.join(File.dirname(__FILE__), 'probe_tap_adapter.rb')
$output_dir = base
pdk = '/foss/pdks/ihp-sg13g2'
root = File.join(pdk, 'libs.ref/sg13g2_io')
libraries = %w[cdl/sg13g2_io.cdl spice/sg13g2_io.spi spice/sg13g2_io.spice doc/README.md]
docs = libraries.to_h do |name|
  path = File.join(root, name)
  lines = File.readlines(path)
  [name, {sha256: Digest::SHA256.file(path).hexdigest,
          global_lines: lines.each_with_index.select { |line, _| line =~ /^\s*\.global\b/i }.map { |line, i| [i+1, line.strip] },
          substrate_lines: lines.each_with_index.select { |line, _| line.downcase.include?('sub!') }.map { |line, i| [i+1, line.strip] }}]
end
original = File.read($original)
io = File.read(File.join(root, 'cdl/sg13g2_io.cdl'))
chunk = original.split("* BEGIN_SOURCE sg13g2_io.cdl\n",2)[1].split("\n* END_SOURCE sg13g2_io.cdl\n",2)[0]
raise 'Original IO assembly did not retain full bytes' unless chunk == io
controls = []
[['absent',''],['explicit','.GLOBAL sub!'],['wrong_name','.GLOBAL other!']].each do |name, declaration|
  path = File.join(base, "scope_#{name}.cir")
  text = "* Isolated reader scope control, not chip reference\n#{declaration}\n.SUBCKT C A\nRR1 A sub! A rppd w=1u l=2u\n.ENDS C\n.SUBCKT TOP A B\nX1 A C\nX2 B C\n.ENDS TOP\n"
  File.write(path, text)
  nl = RBA::Netlist.new
  nl.read(path, RBA::NetlistSpiceReader.new(CustomReader.new))
  nl.flatten
  c = nl.circuit_by_name('TOP')
  resistors = c.each_device.to_a
  raise 'Control device inventory' unless resistors.size == 2
  terminals = resistors.map { |d| d.device_class.terminal_definitions.to_h { |t| [t.name, d.net_for_terminal(t.name).expanded_name] } }
  substrate = terminals.map { |row| row.values.find { |n| n.upcase.include?('SUB!') } }
  expected = name == 'explicit' ? 1 : 2
  raise 'Global scope control failed' unless substrate.none?(&:nil?) && substrate.uniq.size == expected
  controls << {case: name, input_sha256: Digest::SHA256.file(path).hexdigest,
                actual_terminals: terminals, substrate_net_count: substrate.uniq.size,
                parameters: resistors.map { |d| d.device_class.parameter_definitions.to_h { |p| [p.name,d.parameter(p.name)] } },
                status: 'passed exact expected scope'}
end
nl = RBA::Netlist.new
nl.read($adapted, RBA::NetlistSpiceReader.new(CustomReader.new))
nl.flatten
c = nl.circuit_by_name('PLACED_CORE_NOT_CONNECTED_FULLCHIP')
taps = c.each_device.select { |d| d.device_class.name.downcase == 'ptap1' }.map do |d|
  {name: d.expanded_name,
   terminals: d.device_class.terminal_definitions.to_h { |t| [t.name,d.net_for_terminal(t.name).expanded_name] },
   parameters: d.device_class.parameter_definitions.to_h { |p| [p.name,d.parameter(p.name)] }}
end
raise '386 source tap occurrence identity changed' unless taps.size == 386
report = {status: 'passed source scope observation; intended global contract unresolved',
          source_sha256: Digest::SHA256.file($original).hexdigest,
          adapter_sha256: Digest::SHA256.file($adapted).hexdigest,
          script_sha256: Digest::SHA256.file(__FILE__).hexdigest,
          library_evidence: docs, full_IO_chunk_byte_identity: true,
          missing_global_is_fullchip_assembly_omission: false,
          exact_reader_controls: controls, all_reachable_source_taps: taps,
          source_WELL_nets: taps.group_by { |d| d[:terminals]['WELL'] }.transform_values(&:size),
          source_TIE_nets: taps.group_by { |d| d[:terminals]['TIE'] }.transform_values(&:size),
          global_reference_adapter: 'not run', source_intent_qualification: 'not run',
          new_native_extraction: 'not run', analog_simulation: 'not applicable'}
File.write(File.join(base, 'summary.json'), JSON.pretty_generate(report)+"\n")
puts JSON.pretty_generate(report.reject { |k,_| [:library_evidence,:all_reachable_source_taps,:source_WELL_nets].include?(k) })
