// Disassemble + print listing for an address range.
// Usage: -postScript DumpRange.java 0x108d07b0 0x108d08a0
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.CodeUnit;
import ghidra.program.model.listing.Listing;

public class DumpRange extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        var space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Address lo = space.getAddress(args[0]);
        Address hi = space.getAddress(args[1]);
        disassemble(lo);
        Listing listing = currentProgram.getListing();
        var it = listing.getCodeUnits(new AddressSet(lo, hi), true);
        while (it.hasNext() && !monitor.isCancelled()) {
            CodeUnit cu = it.next();
            println(String.format("%s  %-28s ; %s", cu.getAddress(), cu.toString(),
                cu.getComment(0) != null ? cu.getComment(0) : ""));
        }
    }
}
