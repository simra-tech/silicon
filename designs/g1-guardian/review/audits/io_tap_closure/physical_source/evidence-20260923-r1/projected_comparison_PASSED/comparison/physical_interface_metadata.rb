# Source/geometry-bound diagnostic pin metadata projection, never net joining.
module PhysicalInterfaceMetadata
  def self.graph(circuit)
    nets = circuit.each_net.map { |n| [n.property('G1_DIAGNOSTIC_NET_ID'), n.cluster_id, n.name] }.sort
    devices = circuit.each_device.map do |d|
      [d.id, d.expanded_name, d.device_class.name,
       d.device_class.parameter_definitions.map { |p| [p.name, [d.parameter(p.name)].pack('G').unpack1('H*')] },
       d.device_class.terminal_definitions.map { |t| [t.name, d.net_for_terminal(t.name).property('G1_DIAGNOSTIC_NET_ID')] }]
    end
    {sha256: Digest::SHA256.hexdigest(JSON.generate([nets, devices])), nets: nets.size, devices: devices.size}
  end

  def self.pins(circuit)
    circuit.each_pin.map { |p| [p.id, p.name, circuit.net_for_pin(p.id).property('G1_DIAGNOSTIC_NET_ID')] }
  end

  def self.replace(circuit, rows, nets)
    circuit.each_pin.to_a.reverse_each do |p|
      circuit.disconnect_pin(p.id)
      circuit.remove_pin(p.id)
    end
    rows.each do |name, net_id|
      pin = circuit.create_pin(name)
      circuit.connect_pin(pin.id, nets.fetch(net_id))
    end
  end

  def self.reciprocal_links(circuit)
    expected = pins(circuit).map { |id,name,net| [net,id,name] }.sort
    observed = []
    circuit.each_net do |net|
      net.each_pin do |link|
        pin = link.pin
        raise 'Dangling reciprocal pin entry' unless pin && circuit.pin_by_id(link.pin_id)
        observed << [net.property('G1_DIAGNOSTIC_NET_ID'), link.pin_id, pin.name]
      end
    end
    raise 'Reciprocal net/pin metadata differs' unless observed.sort == expected
    {status: 'passed exact bidirectional pin references', count: observed.size,
     sha256: Digest::SHA256.hexdigest(JSON.generate(observed.sort))}
  end

  def self.apply(circuit, path, source_pins)
    raise 'Physical certificate changed' unless Digest::SHA256.file(path).hexdigest == '698a0b00ade4dcb88e6b102593ed9945707a4df18582fdf364adcf9639e92011'
    proof = JSON.parse(File.read(path))
    raise 'Physical certificate incomplete' unless proof['status'].start_with?('passed read-only 24 physical ports / 22 distinct') && proof['ports'].size == 24
    expected = proof['logical_bindings']
    raise 'Wrong source interface' unless source_pins.size == 22 && source_pins.sort == expected.keys.sort
    # Reconstruct the candidate map from all actual geometric probes, rather
    # than accepting its summary blindly. Duplicate physical supplies agree.
    actual = {}
    proof['ports'].each do |port|
      identities = port['probes'].map { |p| [p.fetch('net').fetch('circuit'), p.fetch('net').fetch('cluster_id')] }.uniq
      raise 'Physical port ambiguity' unless identities.size == 1
      raise 'Repeated source port disagreement' if actual.key?(port['pin']) && actual[port['pin']] != identities[0]
      actual[port['pin']] = identities[0]
    end
    valid = lambda do |mapping|
      mapping.keys.sort == source_pins.sort && mapping.values.uniq.size == 22 && mapping == actual
    end
    raise 'Certificate self-inconsistency' unless valid.call(expected)
    controls = []
    %w[swapped missing duplicated].each do |kind|
      bad = Marshal.load(Marshal.dump(expected))
      first, second = source_pins.first(2)
      case kind
      when 'swapped' then bad[first], bad[second] = bad[second], bad[first]
      when 'missing' then bad.delete(first)
      when 'duplicated' then bad[first] = bad[second]
      end
      raise 'Physical-map negative control accepted' if valid.call(bad)
      controls << {case: kind, status: 'passed rejected corrupt physical mapping'}
    end
    nets = circuit.each_net.to_h { |n| [n.property('G1_DIAGNOSTIC_NET_ID'), n] }
    raise 'Electrical net identity collision' unless nets.size == circuit.each_net.to_a.size
    proposed = source_pins.map do |name|
      top, cluster = expected.fetch(name)
      raise 'Wrong physical top binding' unless top == circuit.name
      found = nets.values.select { |n| n.property('G1_ORIGINAL_PARENT_CLUSTER') == cluster }
      raise "Nonunique original parent net for #{name}" unless found.size == 1
      [name, found[0].property('G1_DIAGNOSTIC_NET_ID')]
    end
    before, original = graph(circuit), pins(circuit)
    links = {before: reciprocal_links(circuit)}
    raise 'Original promoted interface changed' unless original.size == 50
    replace(circuit, proposed, nets)
    raise 'Metadata projection changed electrical graph' unless graph(circuit) == before
    raise 'Physical interface pairing changed' unless pins(circuit).map { |_,name,net| [name,net] } == proposed
    projected = pins(circuit)
    links[:projected] = reciprocal_links(circuit)
    # KLayout pin IDs monotonically allocate and cannot be reissued. Reverse
    # proof restores exact logical metadata (order/name/net identity), not IDs.
    old_logical = original.map { |_,name,net| [name,net] }
    replace(circuit, old_logical, nets)
    restored = pins(circuit)
    links[:reverse] = reciprocal_links(circuit)
    raise 'Reverse pin metadata failed' unless restored.map { |_,name,net| [name,net] } == old_logical
    raise 'Reverse changed electrical graph' unless graph(circuit) == before
    replace(circuit, proposed, nets)
    raise 'Final graph changed' unless graph(circuit) == before
    raise 'Final source port metadata changed' unless pins(circuit).map { |_,name,net| [name,net] } == proposed
    links[:final] = reciprocal_links(circuit)
    {status: 'passed isolated physical-interface metadata controls; not native LVS acceptance',
     certificate_sha256: Digest::SHA256.file(path).hexdigest,
     graph_before_after_reverse_final: before, all_net_IDs_names_device_parameters_terminal_incidences_exact: true,
     original_pins: original, first_projected_pins: projected, reverse_restored_pins: restored,
     final_pins: pins(circuit), exact_logical_reverse: true, numeric_pin_ID_reverse: 'not applicable: API allocates new metadata IDs',
     reciprocal_pin_integrity: links, electrical_wrapper_objects: 'preserved throughout metadata projection',
     negative_controls: controls, source_device_or_net_change: false, implicit_joins: false}
  end
end
