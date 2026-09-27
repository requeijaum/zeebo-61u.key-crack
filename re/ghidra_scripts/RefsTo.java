// List code references to given data addresses, optionally filtered to
// callers inside a [lo,hi) range. Also prints string bytes at each target.
// Usage: -postScript RefsTo.java 0x<target>[,...] [caller_lo-caller_hi]
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class RefsTo extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            println("[ERR] pass target addresses");
            return;
        }
        var space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        var fm = currentProgram.getFunctionManager();
        long lo = 0, hi = Long.MAX_VALUE;
        int n = args.length;
        if (args[n - 1].contains("-")) {
            String[] r = args[n - 1].split("-");
            lo = Long.decode(r[0]);
            hi = Long.decode(r[1]);
            n--;
        }
        for (int i = 0; i < n; i++) {
            Address t = space.getAddress(args[i]);
            String preview = "";
            try {
                byte[] b = new byte[32];
                int got = currentProgram.getMemory().getBytes(t, b);
                StringBuilder sb = new StringBuilder();
                for (int k = 0; k < got && b[k] != 0; k++) {
                    sb.append((b[k] >= 32 && b[k] < 127) ? (char) b[k] : '.');
                }
                preview = sb.toString();
            } catch (Exception e) {
                preview = "?";
            }
            println("[TARGET] " + t + " \"" + preview + "\"");
            int c = 0;
            for (Reference ref : getReferencesTo(t)) {
                Address from = ref.getFromAddress();
                long f = from.getOffset();
                if (f < lo || f >= hi) {
                    continue;
                }
                Function fn = fm.getFunctionContaining(from);
                println("      ref from " + from + " in " +
                    (fn != null ? (fn.getName() + "@" + fn.getEntryPoint()) : "nofunc"));
                if (++c > 40) {
                    println("      ... truncated");
                    break;
                }
            }
            if (c == 0) {
                println("      (no refs in range)");
            }
        }
    }
}
