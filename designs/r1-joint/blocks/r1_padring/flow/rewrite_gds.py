# Rewrite a GDS without timestamps so that equal content gives equal bytes.  klayout -b -r rewrite_gds.py -rd i=<in> -rd o=<out>
import pya, hashlib
ly = pya.Layout(); ly.read(i)
o_ = pya.SaveLayoutOptions(); o_.format = 'GDS2'; o_.gds2_write_timestamps = False; o_.gds2_write_cell_properties = False
ly.write(o, o_)
print(ly.top_cell().name, ly.cells(), hashlib.sha256(open(o,'rb').read()).hexdigest())
