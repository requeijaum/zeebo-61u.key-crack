// Decompile the function containing a given hex address and print the C.
// Usage (headless): analyzeHeadless <proj> <name> -process <file> -noanalysis
//   -scriptPath <dir> -postScript DecompileAt.java 0x10ee18
// @category Analysis
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.util.task.ConsoleTaskMonitor;

public class DecompileAt extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            println("[ERR] pass a hex address, e.g. 0x10ee18");
            return;
        }
        long addr = Long.decode(args[0]);
        var space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Function func = currentProgram.getFunctionManager().getFunctionContaining(space.getAddress(addr));
        if (func == null) {
            func = currentProgram.getFunctionManager().getFunctionAt(space.getAddress(addr));
        }
        if (func == null) {
            println("[ERR] no function at/containing " + Long.toHexString(addr));
            return;
        }
        println("[DECOMPILE] " + func.getName() + " entry=" + func.getEntryPoint() +
                " body=" + func.getBody().getMinAddress() + ".." + func.getBody().getMaxAddress());
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        var res = di.decompileFunction(func, 90, new ConsoleTaskMonitor());
        if (res != null && res.decompileCompleted()) {
            println(res.getDecompiledFunction().getC());
        } else {
            println("[ERR] decompile failed");
        }
    }
}
