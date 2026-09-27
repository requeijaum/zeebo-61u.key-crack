// Force Thumb disassembly over a range and print it.
// Usage: -postScript DumpThumb.java 0x108d07b0 0x108d0880
// @category Analysis
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.lang.Register;
import ghidra.program.model.listing.CodeUnit;
import java.math.BigInteger;

public class DumpThumb extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        var space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        Address lo = space.getAddress(args[0]);
        Address hi = space.getAddress(args[1]);
        AddressSet set = new AddressSet(lo, hi);
        // Clear conflicting (ARM-misdecoded) code units first.
        currentProgram.getListing().clearCodeUnits(lo, hi, true);
        // Force Thumb mode over the range.
        Register tmode = currentProgram.getProgramContext().getRegister("TMode");
        if (tmode == null) {
            println("[ERR] no TMode register");
            return;
        }
        ghidra.program.model.lang.RegisterValue rv =
            new ghidra.program.model.lang.RegisterValue(tmode, BigInteger.ONE);
        currentProgram.getProgramContext().setRegisterValue(lo, hi, rv);
        disassemble(lo);
        var it = currentProgram.getListing().getCodeUnits(set, true);
        while (it.hasNext() && !monitor.isCancelled()) {
            CodeUnit cu = it.next();
            println(String.format("%s  %s", cu.getAddress(), cu.toString()));
        }
    }
}
