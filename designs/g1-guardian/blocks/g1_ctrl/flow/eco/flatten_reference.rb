# Flatten a (projected) chip CDL into the flat comparison-only reference used by the
# chip's projected LVS. Same method as review/audits/io_tap_closure/physical_source/
# integration_purefill/flatten_rz_reference.rb (stock PDK LVS reader/writer, flatten,
# drop unreachable library circuits, fix the stock writer's numeric-leading custom
# device names, exact roundtrip compare), without its input-hash lock.
#   klayout -b -r flatten_reference.rb -rd source=<cdl> -rd output=<flat.cdl> -rd top=<top> \
#     [-rd compare=<existing flat cdl>]
require 'json'
require 'digest'
require 'logger'
raise 'arguments' unless $source && $output && $top
pdk = '/foss/pdks/ihp-sg13g2'
raise 'PDK changed' unless File.read(File.join(pdk, 'COMMIT')).strip == '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
def logger; @g1_logger ||= Logger.new($stdout); end
def dbu; 0.001; end
SERIES_RES = true
PARALLEL_RES = true
rules = File.join(pdk, 'libs.tech/klayout/tech/lvs/rule_decks')
%w[globals.lvs custom_reader.lvs custom_writer.lvs custom_devices.lvs custom_combiner.lvs
   custom_extractor.lvs custom_mim_extractor.lvs custom_bjt_extractor.lvs
   custom_isolbox_extractor.lvs].each { |n| load File.join(rules, n) }
def read_net(path)
  n = RBA::Netlist.new
  n.read(path, RBA::NetlistSpiceReader.new(CustomReader.new))
  n
end
top_up = $top.upcase
flat = read_net($source)
raise 'top missing' unless flat.circuit_by_name(top_up)
flat.flatten
ft = flat.circuit_by_name(top_up)
raise 'flat top invalid' unless ft.each_subcircuit.to_a.empty?
flat.each_circuit.reject { |c| c.name == top_up }.each { |c| flat.remove(c) }
writer = RBA::NetlistSpiceWriter.new(CustomWriter.new)
writer.use_net_names = true
writer.with_comments = true
flat.write($output, writer)
prefix = {'CAP_CMIM'=>'C','DANTENNA'=>'D','DPANTENNA'=>'D','NPN13G2'=>'Q','PTAP1'=>'R','RHIGH'=>'R','RPPD'=>'R'}
model = nil
fixed = Hash.new(0)
lines = File.readlines($output).map do |line|
  model = Regexp.last_match(1).strip if line =~ /^\* device instance .* (\S+)\s*$/
  if line =~ /^\d/
    raise "unexpected custom class #{model}" unless prefix.key?(model)
    fixed[model] += 1
    prefix.fetch(model) + line
  else
    line
  end
end
File.write($output, lines.join)
def compare(a, b, top)
  xref = RBA::NetlistCrossReference.new
  cmp = RBA::NetlistComparer.new
  cmp.max_resistance = 1e9
  cmp.min_capacitance = 1e-18
  ok = cmp.compare(a, b, xref)
  pairs = {}
  xref.each_circuit_pair do |cp|
    next unless cp.first && cp.first.name == top
    pairs[:circuit] = cp.status.to_s
    %i[device net pin].each do |k|
      c = Hash.new(0)
      xref.send("each_#{k}_pair", cp) { |p| c[p.status.to_s] += 1 }
      pairs[k] = c
    end
  end
  [ok, pairs]
end
round = read_net($output)
rt_ok, rt_pairs = compare(flat, round, top_up)
rep = {source: $source, source_sha256: Digest::SHA256.file($source).hexdigest, output: $output,
       output_sha256: Digest::SHA256.file($output).hexdigest, top: top_up,
       pins: ft.each_pin.to_a.size, devices: ft.each_device.to_a.size, writer_prefix_fixes: fixed,
       roundtrip_match: rt_ok, roundtrip_pairs: rt_pairs}
if $compare
  other = read_net($compare)
  ok, pairs = compare(round, other, top_up)
  rep[:compare_with] = $compare
  rep[:compare_match] = ok
  rep[:compare_pairs] = pairs
end
File.write($output + '.json', JSON.pretty_generate(rep) + "\n")
puts JSON.generate(rep)
raise 'roundtrip mismatch' unless rt_ok
