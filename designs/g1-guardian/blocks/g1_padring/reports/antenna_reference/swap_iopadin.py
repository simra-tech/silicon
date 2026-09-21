import pya
ly=pya.Layout(); ly.read("<ring-1200 final GDS, sha256 f04ba54d…>")
old=pya.Layout(); old.read("build/sources/ihp-sg13g2-ams-chip-template/ip/sg13g2_io_custom/gds/sg13g2_io.gds")
c=ly.cell("sg13g2_IOPadIn"); assert c is not None
# clear the cell and copy the template's version into it
c.clear()
c.copy_tree(old.cell("sg13g2_IOPadIn"))
print("swapped sg13g2_IOPadIn; instances in top:", sum(1 for i in ly.cell("g1_chip_top").each_inst() if i.cell.name=="sg13g2_IOPadIn"))
ly.write("reports/antenna_reference/g1_1200_oldIOPadIn.gds")
