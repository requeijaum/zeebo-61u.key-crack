// Disassemble + create function at a hex address, then decompile it.
// Usage: -postScript DecompileRaw.java 0x108d08d0
// @category Analysis
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.util.task.ConsoleTaskMonitor;

public class DecompileRaw extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            println("[ERR] pass a hex address");
            return;
        }
        long addr = Long.decode(args[0]);
        var space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        var a = space.getAddress(addr);
        disassemble(a);
        Function func = currentProgram.getFunctionManager().getFunctionContaining(a);
        if (func == null) {
            func = createFunction(a, null);
        }
        if (func == null) {
            println("[ERR] could not create function at " + args[0]);
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
