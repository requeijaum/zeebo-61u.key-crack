// Find arbitrary strings and their code xrefs (literal-pool aware: also
// reports references to cells within +-16 bytes of each hit).
// Usage: -postScript FindStr.java <str1> [<str2> ...]
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class FindStr extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            println("[ERR] pass strings to find");
            return;
        }
        var mem = currentProgram.getMemory();
        var fm = currentProgram.getFunctionManager();
        for (String t : args) {
            byte[] needle = t.getBytes("UTF-8");
            Address start = mem.getMinAddress();
            Address found;
            int n = 0;
            while ((found = mem.findBytes(start, needle, null, true, monitor)) != null) {
                if (++n > 6) {
                    println("[STR] \"" + t + "\" ... too many, truncated");
                    break;
                }
                println("[STR] \"" + t + "\" @ " + found);
                // xrefs to the string and to nearby literal cells
                for (int d = -16; d <= 0; d += 4) {
                    Address cell = found.add(d);
                    for (Reference ref : getReferencesTo(cell)) {
                        Address from = ref.getFromAddress();
                        Function f = fm.getFunctionContaining(from);
                        println("      xref to " + cell + " from " + from + " in " +
                            (f != null ? (f.getName() + "@" + f.getEntryPoint()) : "nofunc"));
                    }
                }
                start = found.add(1);
                if (monitor.isCancelled()) return;
            }
            if (n == 0) {
                println("[STR] \"" + t + "\" NOT FOUND");
            }
        }
    }
}
