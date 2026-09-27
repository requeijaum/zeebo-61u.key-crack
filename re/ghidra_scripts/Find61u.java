// Find 61u.key / 61s.dat string references and the functions using them.
// Usage (headless): analyzeHeadless <projDir> <proj> -process <file> -noanalysis
//   -scriptPath re/ghidra_scripts -postScript Find61u.java
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class Find61u extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] targets = {
            "fs:/mcp/61u.key", "fs:/card0/61u.key", "/61u.key",
            "lctsys/61s.dat", "fs:/mcp/lctsys/61s.dat",
            "OEM_LCTSystemCtl"
        };
        for (String t : targets) {
            boolean any = false;
            // Memory search for the string bytes.
            var mem = currentProgram.getMemory();
            byte[] needle = t.getBytes("UTF-8");
            Address found = null;
            Address start = mem.getMinAddress();
            while ((found = mem.findBytes(start, needle, null, true, monitor)) != null) {
                any = true;
                println("[STR] \"" + t + "\" @ " + found);
                for (Reference ref : getReferencesTo(found)) {
                    Address from = ref.getFromAddress();
                    Function f = currentProgram.getFunctionManager().getFunctionContaining(from);
                    println("      xref from " + from + " in " +
                        (f != null ? ("FUNC " + f.getName() + " entry=" + f.getEntryPoint()) : "no-function"));
                }
                start = found.add(1);
                if (monitor.isCancelled()) break;
            }
            if (!any) {
                println("[STR] \"" + t + "\" NOT FOUND");
            }
        }
    }
}
