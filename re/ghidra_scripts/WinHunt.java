// Report instructions with outgoing refs into given [lo,hi) windows.
// Usage: -postScript WinHunt.java 0x1035a000-0x1035c000 [0x...-0x... ...]
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import java.util.ArrayList;
import java.util.List;

public class WinHunt extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            println("[ERR] pass lo-hi windows");
            return;
        }
        List<long[]> wins = new ArrayList<>();
        for (String a : args) {
            String[] r = a.split("-");
            wins.add(new long[] { Long.decode(r[0]), Long.decode(r[1]) });
        }
        var fm = currentProgram.getFunctionManager();
        int scanned = 0, reported = 0;
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            if (!block.isExecute()) {
                continue;
            }
            InstructionIterator it = currentProgram.getListing()
                .getInstructions(new AddressSet(block.getStart(), block.getEnd()), true);
            while (it.hasNext() && !monitor.isCancelled()) {
                Instruction insn = it.next();
                if (++scanned % 1000000 == 0) {
                    println("[WinHunt] scanned " + scanned);
                }
                for (Reference ref : insn.getReferencesFrom()) {
                    long t = ref.getToAddress().getOffset();
                    for (long[] w : wins) {
                        if (t >= w[0] && t < w[1]) {
                            Function f = fm.getFunctionContaining(insn.getAddress());
                            println("[HIT] " + insn.getAddress() + " " + insn.toString() +
                                " -> " + ref.getToAddress() + " in " +
                                (f != null ? (f.getName() + "@" + f.getEntryPoint()) : "nofunc"));
                            if (++reported > 120) {
                                println("[WinHunt] cap reached");
                                return;
                            }
                        }
                    }
                }
            }
        }
        println("[WinHunt] done scanned=" + scanned + " reported=" + reported);
    }
}
