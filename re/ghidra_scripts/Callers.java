// Print code references TO given function addresses (callers).
// Usage: -postScript Callers.java 0x108d07a0 0x1014e902
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class Callers extends GhidraScript {
    @Override
    public void run() throws Exception {
        var space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        var fm = currentProgram.getFunctionManager();
        for (String a : getScriptArgs()) {
            Address addr = space.getAddress(a);
            Function target = fm.getFunctionAt(addr);
            if (target == null) {
                target = fm.getFunctionContaining(addr);
            }
            println("[CALLERS] " + a + " -> " +
                (target != null ? (target.getName() + "@" + target.getEntryPoint()) : "nofunc"));
            for (Reference ref : getReferencesTo(addr)) {
                Address from = ref.getFromAddress();
                Function f = fm.getFunctionContaining(from);
                println("      called from " + from + " in " +
                    (f != null ? (f.getName() + "@" + f.getEntryPoint()) : "nofunc") +
                    " type=" + ref.getReferenceType());
            }
        }
    }
}
