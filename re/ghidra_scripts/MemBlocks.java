// Print memory blocks (name, start-end, rwx, initialized).
// @category Analysis
import ghidra.app.script.GhidraScript;

public class MemBlocks extends GhidraScript {
    @Override
    public void run() throws Exception {
        for (var b : currentProgram.getMemory().getBlocks()) {
            println(String.format("[BLK] %-28s %s..%s %s%s%s %s",
                b.getName(), b.getStart(), b.getEnd(),
                b.isRead() ? "r" : "-", b.isWrite() ? "w" : "-",
                b.isExecute() ? "x" : "-",
                b.isInitialized() ? "init" : "uninit"));
        }
    }
}
