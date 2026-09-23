# Read-only reader semantics probe. Generated fixtures are not replacement sources.
require 'json'
require 'digest'
require 'logger'
require 'fileutils'
def logger
  @probe_logger ||= Logger.new($stdout)
end
def dbu
  0.001
end
pdk = '/foss/pdks/ihp-sg13g2'
raise 'PDK identity' unless File.read(File.join(pdk, 'COMMIT')).strip == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
raise 'Output required' unless $output_dir
raise 'Preserve old output' if File.exist?($output_dir)
rules = File.join(pdk, 'libs.tech/klayout/tech/lvs/rule_decks')
rule_files = %w[globals.lvs custom_reader.lvs custom_combiner.lvs custom_devices.lvs]
rule_files.each { |file| load File.join(rules, file) }
source = File.join(pdk, 'libs.ref/sg13g2_io/cdl/sg13g2_io.cdl')
raise 'Source identity' unless Digest::SHA256.file(source).hexdigest == '7a30e902099e8a8f85e0ae853167904df3793357a793a7b4dc82237b72b3eec4'
FileUtils.mkdir_p($output_dir)
FileUtils.cp(__FILE__, File.join($output_dir, 'worker_snapshot.rb'))
text = File.read(source)
rows = %w[sg13g2_io_inv_x1 sg13g2_Filler10000].map do |cell|
  literal = text.match(/^\.SUBCKT\s+#{cell}\s.*?^\.ENDS[^\n]*\n/im)[0]
  edits = []
  normalized = literal.gsub(/^(\s*)(X\S+)(\s+\S+\s+\S+\s+[pn]tap1\s+.*)$/i) do
    edits << {instance: $2, exact_unchanged_node_model_parameter_suffix: $3}
    "#{$1}R_PROBE_#{$2}#{$3}"
  end
  fixture = File.join($output_dir, "#{cell}_prefix_only.cdl")
  File.write(fixture, normalized)
  netlist = RBA::Netlist.new
  netlist.read(fixture, RBA::NetlistSpiceReader.new(CustomReader.new))
  circuit = netlist.circuit_by_name(cell.upcase)
  raise 'Missing circuit' unless circuit
  taps = []
  circuit.each_device do |dev|
    next unless dev.device_class.name.downcase.include?('tap')
    klass = dev.device_class
    taps << {instance: dev.name, A_um2: dev.parameter('A'), P_um: dev.parameter('P'),
             TIE: dev.net_for_terminal(klass.terminal_id('TIE')).name,
             WELL: dev.net_for_terminal(klass.terminal_id('WELL')).name}
  end
  raise 'Tap count' unless taps.size == edits.size
  {cell: cell, literal_cell_sha256: Digest::SHA256.hexdigest(literal),
   prefix_only_fixture_sha256: Digest::SHA256.hexdigest(normalized), edits: edits, taps: taps}
end
File.write(File.join($output_dir, 'parsed_before_assertions.json'), JSON.pretty_generate(rows) + "\n")
raise 'Literal unitless P changed' unless rows[0][:taps][0][:P_um] == 3_160_000.0
raise 'PERIM alias' unless rows[1][:taps].map { |r| r[:P_um] }.sort == [15.42e-6 * 1e6, 240.72e-6 * 1e6]
report = {status: 'passed reader semantics only', source_sha256: Digest::SHA256.file(source).hexdigest,
          rule_sha256: rule_files.to_h { |file| [file, Digest::SHA256.file(File.join(rules, file)).hexdigest] },
          rows: rows, checks: {unitless_P_read_as_SI: 'passed', PERIM_alias: 'passed',
          native_LVS: 'not run', electrical_equivalence: 'not run', rule_model_source_changes: 'not run'}}
File.write(File.join($output_dir, 'summary.json'), JSON.pretty_generate(report) + "\n")
puts JSON.pretty_generate(report)
