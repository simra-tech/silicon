# Read-only stock-reader probe. No layout extraction or rule modification.
require 'json'
require 'digest'
require 'logger'

def logger
  @probe_logger ||= Logger.new($stdout)
end

def dbu
  0.001
end

pdk = '/foss/pdks/ihp-sg13g2'
raise 'PDK identity mismatch' unless File.read(File.join(pdk, 'COMMIT')).strip == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
rules = File.join(pdk, 'libs.tech/klayout/tech/lvs/rule_decks')
%w[globals.lvs custom_reader.lvs custom_combiner.lvs custom_devices.lvs].each { |file| load File.join(rules, file) }

def inventory(netlist)
  result = []
  netlist.each_circuit do |circuit|
    devices = []
    circuit.each_device do |device|
      klass = device.device_class
      row = {name: device.name, model: klass.name}
      if %w[ptap1 ntap1].include?(klass.name.downcase)
        row[:area_um2] = device.parameter('A')
        row[:perimeter_um] = device.parameter('P')
        row[:tie] = device.net_for_terminal(klass.terminal_id('TIE')).name
        row[:well] = device.net_for_terminal(klass.terminal_id('WELL')).name
      end
      devices << row
    end
    subcircuits = []
    circuit.each_subcircuit { |sub| subcircuits << {name: sub.name, reference: sub.circuit_ref.name} }
    result << {circuit: circuit.name, devices: devices, subcircuits: subcircuits}
  end
  result
end

raise 'Specify -rd input_dir=... -rd output=...' unless $input_dir && $output
raise 'Preserve prior output' if File.exist?($output)
rows = []
%w[sg13g2_Filler400 sg13g2_LevelUpInv sg13g2_RCClampInverter].each do |cell|
  %w[original normalized].each do |variant|
    path = File.join($input_dir, "#{cell}_#{variant}.cdl")
    netlist = RBA::Netlist.new
    netlist.read(path, RBA::NetlistSpiceReader.new(CustomReader.new))
    before = inventory(netlist)
    netlist.simplify
    after = inventory(netlist)
    rows << {cell: cell, variant: variant, input_sha256: Digest::SHA256.file(path).hexdigest,
             before_simplify: before, after_simplify: after}
  end
end
report = {scope: 'Exact unchanged stock reader parses source and syntax-normalized cell references; no layout extraction.',
          stock_rule_sha256: %w[globals.lvs custom_reader.lvs custom_combiner.lvs custom_devices.lvs].to_h { |file| [file, Digest::SHA256.file(File.join(rules, file)).hexdigest] },
          rows: rows, stock_LVS: 'not run'}
File.write($output, JSON.pretty_generate(report) + "\n")
puts JSON.pretty_generate(report)
