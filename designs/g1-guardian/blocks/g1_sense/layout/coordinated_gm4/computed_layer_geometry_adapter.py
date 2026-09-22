#!/usr/bin/env python3
"""Isolated generic exact-computed-layer selector; installed package stays unchanged."""
import klayout.db as kdb
from klayout_pex.fastercap.fastercap_input_builder import FasterCapInputBuilder


class ExactComputedLayerBuilder(FasterCapInputBuilder):
    def computed_region(self,layer_name):
        pair=self.tech_info.gds_pair_for_computed_layer_name[layer_name]
        layer=self.pex_context.extracted_layers.get(pair)
        if layer is None:return None
        matches=[s.region for s in layer.source_layers if s.lvs_layer_name==layer_name]
        assert len(matches)<=1,('ambiguous computed identity',layer_name,len(matches))
        return matches[0].dup() if matches else None

    def shapes_of_layer(self,layer_name):
        if layer_name in self.tech_info.gds_pair_for_computed_layer_name:
            return self.computed_region(layer_name)
        return super().shapes_of_layer(layer_name)

    def shapes_of_net(self,layer_name,net):
        if layer_name not in self.tech_info.gds_pair_for_computed_layer_name:
            return super().shapes_of_net(layer_name,net)
        region=self.computed_region(layer_name)
        if region is None:return None
        net_name=net.expanded_name() if isinstance(net,kdb.Net) else net
        result=kdb.Region();result.enable_properties()
        iterator,transform=region.begin_shapes_rec()
        while not iterator.at_end():
            shape=iterator.shape()
            if shape.property('net')==net_name:
                polygon=transform*iterator.trans()*shape.polygon
                result.insert(kdb.PolygonWithProperties(polygon,shape.properties()))
            iterator.next()
        return result
