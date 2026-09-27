// Hunt instructions referencing the 61u.key string windows, precisely:
// for every instruction in executable blocks, check outgoing references
// (literal pools included) and movw/movt scalar operands.
// Usage: -scriptPath re/ghidra_scripts -postScript Hunt61u.java
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;

public class Hunt61u extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[][] windows = {
            {0x108d0800L, 0x108d0900L},
            {0x10aff200L, 0x10aff300L},
            {0x11267900L, 0x11267c00L},
            {0x10e9fb00L, 0x10e9fd00L}
        };
        var space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        int scanned = 0;
        int reported = 0;
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            if (!block.isExecute()) {
                continue;
            }
            AddressSet set = new AddressSet(block.getStart(), block.getEnd());
            InstructionIterator it = currentProgram.getListing().getInstructions(set, true);
            while (it.hasNext() && !monitor.isCancelled()) {
                Instruction insn = it.next();
                scanned++;
                if ((scanned % 500000) == 0) {
                    println("[Hunt61u] scanned " + scanned);
                }
                // 1. outgoing references into windows
                for (Reference ref : insn.getReferencesFrom()) {
                    Address to = ref.getToAddress();
                    long t = to.getOffset();
                    for (long[] w : windows) {
                        if (t >= w[0] && t < w[1]) {
                            var f = currentProgram.getFunctionManager()
                                .getFunctionContaining(insn.getAddress());
                            println("[HIT-REF] " + insn.getAddress() + " " + insn.toString() +
                                " -> " + to + " in " +
                                (f != null ? (f.getName() + "@" + f.getEntryPoint()) : "nofunc"));
                            if (++reported > 300) {
                                println("[Hunt61u] hit cap reached");
                                return;
                            }
                        }
                    }
                }
                // 2. movw/movt scalar operands equal to low/high16 of string addrs
                String mn = insn.getMnemonicString();
                if (mn.equals("movw") || mn.equals("movt")) {
                    for (int i = 0; i < insn.getNumOperands(); i++) {
                        Scalar s = insn.getScalar(i);
                        if (s == null) {
                            continue;
                        }
                        long v = s.getValue();
                        long[] probes = {0x08a4L, 0x08b4L, 0xf2e4L, 0xf29cL, 0x7a40L,
                                         0x108dL, 0x10afL, 0x1126L};
                        for (long p : probes) {
                            if (v == p) {
                                var f = currentProgram.getFunctionManager()
                                    .getFunctionContaining(insn.getAddress());
                                println("[HIT-MOV] " + insn.getAddress() + " " + insn.toString() +
                                    " imm=" + Long.toHexString(v) + " in " +
                                    (f != null ? (f.getName() + "@" + f.getEntryPoint()) : "nofunc"));
                                if (++reported > 300) {
                                    println("[Hunt61u] hit cap reached");
                                    return;
                                }
                            }
                        }
                    }
                }
            }
        }
        println("[Hunt61u] done, scanned=" + scanned + " reported=" + reported);
    }
}
