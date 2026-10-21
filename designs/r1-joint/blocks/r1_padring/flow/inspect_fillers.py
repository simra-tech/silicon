# List shapes per layer of the IO filler cells (retained copy in the ring versus PDK cell).
import pya
for path, names in ((ring, ['retained_fullchip_sg13g2_Filler400', 'retained_fullchip_sg13g2_Filler2000', 'sg13g2_Filler200']), (io, ['sg13g2_Filler200', 'sg13g2_Filler400', 'sg13g2_Filler2000'])):
    ly = pya.Layout(); ly.read(path)
    for n in names:
        c = ly.cell(n)
        if c is None: continue
        d = {}
        for li in ly.layer_indexes():
            i = ly.get_info(li); sh = c.shapes(li)
            if sh.size(): d['%d/%d' % (i.layer, i.datatype)] = [sh.size(), sum(1 for s in sh.each() if s.is_text())]
        print(path.rsplit('/', 1)[-1], n, c.bbox().to_s(), d)
