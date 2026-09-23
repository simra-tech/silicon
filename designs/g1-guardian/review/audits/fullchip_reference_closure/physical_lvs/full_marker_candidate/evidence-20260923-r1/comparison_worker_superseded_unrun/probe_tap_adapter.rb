# Pinned unmodified reader control; no geometry/extractor/model changes.
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
# Exact defaults reported by the held original fullchip stock invocation.
# The standalone reader API does not execute sg13g2.lvs switch initialization.
SERIES_RES = true
PARALLEL_RES = true
raise 'Expected original, adapted and output arguments' unless $original && $adapted && $output_dir
raise 'Preserve outputs' if File.exist?($output_dir)
pdk = '/foss/pdks/ihp-sg13g2'
raise 'Wrong PDK' unless File.read(File.join(pdk, 'COMMIT')).strip == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
raise 'Original source changed' unless Digest::SHA256.file($original).hexdigest == 'f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9'
raise 'Adapted source changed' unless Digest::SHA256.file($adapted).hexdigest == '7395c32d170a787dbc81fd10c67148301d168e51f5ac38de3f0866efe5894006'
rules = File.join(pdk, 'libs.tech/klayout/tech/lvs/rule_decks')
stock_program = File.join(pdk, 'libs.tech/klayout/tech/lvs/sg13g2.lvs')
default_definitions = File.readlines(stock_program).grep(/^(SERIES_RES|PARALLEL_RES)\s*=/)
raise 'Stock default definitions not found' unless default_definitions.size == 2
stock_log = File.join(File.dirname(File.dirname($original)), 'fullchip-native-strict-lvs-20260923-r2/reports/sealed_native.log')
raise 'Original engine log changed' unless Digest::SHA256.file(stock_log).hexdigest == 'e1e14cd9e4378f29db70f1b285a924bc11fe5402afbc06233ed274a2d186c2a8'
stock_log_text = File.read(stock_log)
%w[SERIES_RES PARALLEL_RES].each do |name|
  raise 'Stock default log ambiguity' unless stock_log_text.scan(/Selected #{name} option: ([^\r\n]*)/).flatten == ['true']
end
files = %w[globals.lvs custom_reader.lvs custom_writer.lvs custom_devices.lvs
           custom_combiner.lvs custom_extractor.lvs custom_mim_extractor.lvs
           custom_bjt_extractor.lvs custom_isolbox_extractor.lvs]
# Ruby `load` does not expand KLayout's commented %include directives. Load
# the complete stock custom_classes/custom_devices include closure verbatim.
class_manifest = File.join(rules, 'custom_classes.lvs')
closure = %w[custom_classes.lvs]
pending = closure.dup
until pending.empty?
  name = pending.shift
  File.readlines(File.join(rules, name)).each do |line|
    next unless line =~ /^\s*#\s*%include\s+(\S+)/
    child = Regexp.last_match(1)
    next if closure.include?(child)
    closure << child
    pending << child
  end
end
raise 'Incomplete stock include closure' unless (closure - ['custom_classes.lvs']).sort == files.sort
files.each { |name| load File.join(rules, name) }
rule_hashes = files.to_h { |name| [name, Digest::SHA256.file(File.join(rules, name)).hexdigest] }
FileUtils.mkdir_p($output_dir)
FileUtils.cp(__FILE__, File.join($output_dir, 'worker_snapshot.rb'))
snapshots = {}
{original: $original, adapted: $adapted}.each do |view, path|
  nl = RBA::Netlist.new
  nl.read(path, RBA::NetlistSpiceReader.new(CustomReader.new))
  taps = []
  other = {}
  circuit_pins = {}
  nl.each_circuit do |c|
    rows = []
    circuit_pins[c.name] = c.each_pin.map { |pin| [pin.id, pin.name] }
    c.each_device do |dev|
      klass = dev.device_class
      row = {circuit: c.name, name: dev.name, model: klass.name,
             parameters: klass.parameter_definitions.to_h { |p| [p.name, dev.parameter(p.name)] },
             terminals: klass.terminal_definitions.to_h { |t| [t.name, dev.net_for_terminal(t.name)&.name] }}
      if klass.name.downcase.include?('tap')
        taps << row
      else
        rows << row
      end
    end
    other[c.name] = rows unless rows.empty?
  end
  snapshots[view] = {taps: taps, non_tap_devices: other, circuit_pins: circuit_pins}
end
File.write(File.join($output_dir, 'raw_reader.json'), JSON.pretty_generate(snapshots) + "\n")
raise 'Original unexpectedly binds tap primitives' unless snapshots[:original][:taps].empty?
raise 'Expected 63 source tap records' unless snapshots[:adapted][:taps].size == 63
raise 'Non-tap device/model/node/parameter changed' unless snapshots[:original][:non_tap_devices] == snapshots[:adapted][:non_tap_devices]
manifest = JSON.parse(File.read(File.join(File.dirname($adapted), 'summary.json')))
expected = manifest['edits'].to_h { |e| [[e['cell'].upcase, e['adapted_name'][1..]], e] }
raise 'Duplicate adapted identity' unless expected.size == 63
snapshots[:adapted][:taps].each do |tap|
  e = expected.delete([tap[:circuit], tap[:name]])
  raise 'Unexpected tap identity' unless e
  tokens = e['exact_suffix'].split
  raise 'Wrong tap model' unless tap[:model].downcase == tokens[2].downcase
  raise 'Wrong TIE/WELL source order' unless tap[:terminals] == {'TIE' => tokens[0].upcase, 'WELL' => tokens[1].upcase}
  raise 'No positive original A/P interpretation' unless tap[:parameters]['A'] > 0 && tap[:parameters]['P'] > 0
end
raise 'Omitted source taps' unless expected.empty?
snapshots[:adapted][:circuit_pins].each do |name, pins|
  raise 'Declared circuit interface changed' unless snapshots[:original][:circuit_pins][name] == pins
end
raise 'Rule changed' unless files.all? { |name| rule_hashes[name] == Digest::SHA256.file(File.join(rules, name)).hexdigest }
report = {status: 'passed pinned-reader syntax binding only; strict LVS not run',
          source_sha256: Digest::SHA256.file($original).hexdigest,
          adapted_sha256: Digest::SHA256.file($adapted).hexdigest,
          reader_rule_hashes: rule_hashes, script_sha256: Digest::SHA256.file(__FILE__).hexdigest,
          stock_class_include_closure: closure,
          stock_class_manifest_sha256: Digest::SHA256.file(class_manifest).hexdigest,
          stock_default_definitions: default_definitions,
          stock_program_sha256: Digest::SHA256.file(stock_program).hexdigest,
          stock_original_engine_log_sha256: Digest::SHA256.file(stock_log).hexdigest,
          tap_records: 63, source_cell_count: 41,
          checks: {all_original_suffix_bytes: 'passed by separately bound preparation',
                   reader_TIE_WELL_model_identity: 'passed all 63',
                   non_tap_model_parameter_terminal_identity: 'passed',
                   declared_interfaces: 'passed', native_LVS: 'not run',
                   source_A_P_applicability: 'failed retained native discrepancy',
                   new_geometry_or_model_changes: 'not applicable'}}
File.write(File.join($output_dir, 'summary.json'), JSON.pretty_generate(report) + "\n")
puts JSON.pretty_generate(report)
