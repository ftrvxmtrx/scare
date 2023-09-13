#!/usr/bin/python
from __future__ import print_function
from unicorn import *
from unicorn.x86_const import *
from unicorn.arm64_const import *
from unicorn.arm_const import *
from keystone import *
import capstone
from scareconfig import *
import random

def printSplash(splashColSet):
    splashColz = {
    "litepink": (213, 1), 
    "furnace":  (196, 1),
    "aqua":     (27,  1),
    "cerulean": (87,  6),
    "xyber":    (28,  1),
    "sunrise":  (208, 1),
    "haunter":  (103, 6),
    "mew":      (170, 1),
    "articuno": (63,  1),
    "esp":      (63,  6),
    "grey":     (236, 1),
    }
    if splashColSet == "random":
        splashColSet = random.choice(list(splashColz.items()))
        splashColSet = splashColSet[0]
    spc  = splashColz[splashColSet][0]
    mode = splashColz[splashColSet][1] # 1 or 6, 6 would do columns, from 1 to 87
    splash = f"""\x1b[38;5;{spc}m\
┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐\x1b[38;5;{spc+(mode*6)}m
└──────┐│       ┌──────││       │      │\x1b[38;5;{spc+(mode*12)}m
│      ││       │      ││       │──────┘\x1b[38;5;{spc+(mode*18)}m
└──────┘└──────┘└──────┘└       └──────┘\x1b[0m
Simple Configurable Asm REPL && Emulator 
                [v0.3.0]
    """
    print(splash)

helpfile = """
scare Help

/ /? /help                           -- Open help menu
/x /exit /q /quit                    -- Quit the program

/back n                              -- Go back n number of lines
/dis {0xaddress|$register} NUM       -- Disassemble NUM bytes from 0xaddress or $register
/export FILETYPE FILENAME            -- Export machine code as FILETYPE to the FILENAME
                                        FILETYPE List:
                                        - bin
                                        - elf64
                                        - pe32
/info                                -- Info about the emulator state
/l /list                             -- List the current program
/load file.asm                       -- Load listing from file.asm (overwrites current program)
/read {0xaddress|$register} NUM      -- Read NUM bytes from 0xaddress or $register
/write {0xaddress|$register} hexdata -- Write bytes to 0xaddress or $register
/write {0xaddress|$register} ./file  -- Write file data to 0xaddress or $register
/regs                                -- Print register state
/get register [register... ]         -- Print register state
/set register value                  -- Set a register
/reset                               -- Reset the emulator to a clean state
/run                                 -- Run the current program
/save file.asm                       -- Save assembly output to file.asm

[[: Config Commands :]] (Use /c or /config)
NOTE: Run /reset if you are changing emu/* options, otherwise the emulator may not start!

/c               -- Print all config options
/c emu/arch      -- Print Arch Value
/c emu/arch x64  -- Set Arch to x64
/c x86/xmm 1     -- Enable x86/xmm
/c arm64/neon 1  -- Enable arm64/neon
"""


### Register Output Stuff ######################################################
rNames = {
    "arm32" : {
        "r0" : UC_ARM_REG_R0,
        "r1" : UC_ARM_REG_R1,
        "r2" : UC_ARM_REG_R2,
        "r3" : UC_ARM_REG_R3,
        "r4" : UC_ARM_REG_R4,
        "r5" : UC_ARM_REG_R5,
        "r6" : UC_ARM_REG_R6,
        "r7" : UC_ARM_REG_R7,
        "r8" : UC_ARM_REG_R8,
        "r9" : UC_ARM_REG_R9,
        "r10": UC_ARM_REG_R10,
        "r11": UC_ARM_REG_R11,
        "r12": UC_ARM_REG_R12,
        "sp":  UC_ARM_REG_SP,
        "lr":  UC_ARM_REG_LR,
        "pc":  UC_ARM_REG_PC,
        "cpsr":  UC_ARM_REG_CPSR,
    },
    "arm64" : {
        "x0" : UC_ARM64_REG_X0,
        "x1" : UC_ARM64_REG_X1,
        "x2" : UC_ARM64_REG_X2,
        "x3" : UC_ARM64_REG_X3,
        "x4" : UC_ARM64_REG_X4,
        "x5" : UC_ARM64_REG_X5,
        "x6" : UC_ARM64_REG_X6,
        "x7" : UC_ARM64_REG_X7,
        "x8" : UC_ARM64_REG_X8,
        "x9" : UC_ARM64_REG_X9,
        "x10": UC_ARM64_REG_X10,
        "x11": UC_ARM64_REG_X11,
        "x12": UC_ARM64_REG_X12,
        "x13": UC_ARM64_REG_X13,
        "x14": UC_ARM64_REG_X14,
        "x15": UC_ARM64_REG_X15,
        "x16": UC_ARM64_REG_X16,
        "x17": UC_ARM64_REG_X17,
        "x18": UC_ARM64_REG_X18,
        "x19": UC_ARM64_REG_X19,
        "x20": UC_ARM64_REG_X20,
        "x21": UC_ARM64_REG_X21,
        "x22": UC_ARM64_REG_X22,
        "x23": UC_ARM64_REG_X23,
        "x24": UC_ARM64_REG_X24,
        "x25": UC_ARM64_REG_X25,
        "x26": UC_ARM64_REG_X26,
        "x27": UC_ARM64_REG_X27,
        "x28": UC_ARM64_REG_X28,
        "x29": UC_ARM64_REG_X29,
        "x30": UC_ARM64_REG_X30,
        "sp":  UC_ARM64_REG_SP,
        "pc":  UC_ARM64_REG_PC,
        "cpsr":  UC_ARM_REG_CPSR,
    },
    "neon": {
        "v0" : UC_ARM64_REG_V0,
        "v1" : UC_ARM64_REG_V1,
        "v2" : UC_ARM64_REG_V2,
        "v3" : UC_ARM64_REG_V3,
        "v4" : UC_ARM64_REG_V4,
        "v5" : UC_ARM64_REG_V5,
        "v6" : UC_ARM64_REG_V6,
        "v7" : UC_ARM64_REG_V7,
        "v8" : UC_ARM64_REG_V8,
        "v9" : UC_ARM64_REG_V9,
        "v10": UC_ARM64_REG_V10,
        "v11": UC_ARM64_REG_V11,
        "v12": UC_ARM64_REG_V12,
        "v13": UC_ARM64_REG_V13,
        "v14": UC_ARM64_REG_V14,
        "v15": UC_ARM64_REG_V15,
        "v16": UC_ARM64_REG_V16,
        "v17": UC_ARM64_REG_V17,
        "v18": UC_ARM64_REG_V18,
        "v19": UC_ARM64_REG_V19,
        "v20": UC_ARM64_REG_V20,
        "v21": UC_ARM64_REG_V21,
        "v22": UC_ARM64_REG_V22,
        "v23": UC_ARM64_REG_V23,
        "v24": UC_ARM64_REG_V24,
        "v25": UC_ARM64_REG_V25,
        "v26": UC_ARM64_REG_V26,
        "v27": UC_ARM64_REG_V27,
        "v28": UC_ARM64_REG_V28,
        "v29": UC_ARM64_REG_V29,
        "v30": UC_ARM64_REG_V30,
        "v31": UC_ARM64_REG_V31,
    },
    "x86": {
        "eax": UC_X86_REG_EAX,
        "ebx": UC_X86_REG_EBX,
        "ecx": UC_X86_REG_ECX,
        "edx": UC_X86_REG_EDX,
        "esi": UC_X86_REG_ESI,
        "edi": UC_X86_REG_EDI,
        "eip": UC_X86_REG_EIP,
        "esp": UC_X86_REG_ESP,
        "ebp": UC_X86_REG_EBP,
        "eflags": UC_X86_REG_EFLAGS,
    },
    "x64": {
        "rax": UC_X86_REG_RAX,
        "rbx": UC_X86_REG_RBX,
        "rcx": UC_X86_REG_RCX,
        "rdx": UC_X86_REG_RDX,
        "rsi": UC_X86_REG_RSI,
        "rdi": UC_X86_REG_RDI,
        "rip": UC_X86_REG_RIP,
        "rsp": UC_X86_REG_RSP,
        "rbp": UC_X86_REG_RBP,
        "r8":  UC_X86_REG_R8,
        "r9":  UC_X86_REG_R9,
        "r10": UC_X86_REG_R10,
        "r11": UC_X86_REG_R11,
        "r12": UC_X86_REG_R12,
        "r13": UC_X86_REG_R13,
        "r14": UC_X86_REG_R14,
        "r15": UC_X86_REG_R15,
        "rflags": UC_X86_REG_EFLAGS,
    },
    "xmm": {
        "xmm0":  UC_X86_REG_XMM0,
        "xmm1":  UC_X86_REG_XMM1,
        "xmm2":  UC_X86_REG_XMM2,
        "xmm3":  UC_X86_REG_XMM3,
        "xmm4":  UC_X86_REG_XMM4,
        "xmm5":  UC_X86_REG_XMM5,
        "xmm6":  UC_X86_REG_XMM6,
        "xmm7":  UC_X86_REG_XMM7,
        "xmm8":  UC_X86_REG_XMM8,
        "xmm9":  UC_X86_REG_XMM9,
        "xmm10": UC_X86_REG_XMM10,
        "xmm11": UC_X86_REG_XMM11,
        "xmm12": UC_X86_REG_XMM12,
        "xmm13": UC_X86_REG_XMM13,
        "xmm14": UC_X86_REG_XMM14,
        "xmm15": UC_X86_REG_XMM15,
        "xmm16": UC_X86_REG_XMM16,
        "xmm17": UC_X86_REG_XMM17,
        "xmm18": UC_X86_REG_XMM18,
        "xmm19": UC_X86_REG_XMM19,
        "xmm20": UC_X86_REG_XMM20,
        "xmm21": UC_X86_REG_XMM21,
        "xmm22": UC_X86_REG_XMM22,
        "xmm23": UC_X86_REG_XMM23,
        "xmm24": UC_X86_REG_XMM24,
        "xmm25": UC_X86_REG_XMM25,
        "xmm26": UC_X86_REG_XMM26,
        "xmm27": UC_X86_REG_XMM27,
        "xmm28": UC_X86_REG_XMM28,
        "xmm29": UC_X86_REG_XMM29,
        "xmm30": UC_X86_REG_XMM30,
        "xmm31": UC_X86_REG_XMM31,
    },
}

# regFmt - Format register for output
# mu = Emulator Object
# regType = Type of register for custom styling
#     0 - General Purpose
#     1 - Instruction Pointer
#     2 - Stack Pointer
# regSize = The size of the register in bits
# regName = The emulator specific constant, resolved using rNames dict
def regFmt(mu, regType, regSize, regName):
    outRegVal = mu.reg_read(regName)
    if regType == 0:
        outRegColor = cGReg if outRegVal > 0 else cZero
    elif regType == 1:
        outRegColor = cIP
    elif regType == 2:
        outRegColor = cSPtr
    else:
        print(f"Unknown Register Type {regType}")
        return
    if regSize == 8:
        outRegValFmt = f"{outRegVal:02x}"
    elif regSize == 16:
        outRegValFmt = f"{outRegVal:04x}"
    elif regSize == 32:
        outRegValFmt = f"{outRegVal:08x}"
    elif regSize == 64:
        outRegValFmt = f"{outRegVal:016x}"
    elif regSize == 128:
        outRegValFmt = f"{outRegVal:032x}"
    else:
        print("Unknown Register Size!")
        return
    outRegText = f"{outRegColor}{outRegValFmt}{cEnd}"
    return outRegText

def printRegs_arm32(mu, sConfig):
    print(f"{cRegN}  r0: {regFmt(mu,0,32,rNames['arm32']['r0' ])} {cRegN} r1: {regFmt(mu,0,32,rNames['arm32']['r1' ])} {cRegN} r2: {regFmt(mu,0,32,rNames['arm32']['r2' ])} {cRegN} r3: {regFmt(mu,0,32,rNames['arm32']['r3' ])}")
    print(f"{cRegN}  r4: {regFmt(mu,0,32,rNames['arm32']['r4' ])} {cRegN} r5: {regFmt(mu,0,32,rNames['arm32']['r5' ])} {cRegN} r6: {regFmt(mu,0,32,rNames['arm32']['r6' ])} {cRegN} r7: {regFmt(mu,0,32,rNames['arm32']['r7' ])} ")
    print(f"{cRegN}  r8: {regFmt(mu,0,32,rNames['arm32']['r8' ])} {cRegN} r9: {regFmt(mu,0,32,rNames['arm32']['r9' ])} {cRegN}r10: {regFmt(mu,0,32,rNames['arm32']['r10'])} {cRegN}r11: {regFmt(mu,0,32,rNames['arm32']['r11'])}")
    print(f"{cRegN} r12: {regFmt(mu,0,32,rNames['arm32']['r12'])} {cRegN} sp: {regFmt(mu,2,32,rNames['arm32']['sp' ])} {cRegN} lr: {regFmt(mu,0,32,rNames['arm32']['lr' ])} {cRegN} pc: {regFmt(mu,1,32,rNames['arm32']['pc' ])} ")
    print(f"{cRegN}cpsr: {regFmt(mu,0,32,rNames['arm32']['cpsr'] )} ")
    print(cEnd,end="")

def printRegs_arm64(mu, sConfig):
    print(f"{cRegN} x0: {regFmt(mu,0,64,rNames['arm64']['x0' ])} {cRegN}  x1: {regFmt(mu,0,64,rNames['arm64']['x1' ])} {cRegN}  x2: {regFmt(mu,0,64,rNames['arm64']['x2' ])} {cRegN}  x3: {regFmt(mu,0,64,rNames['arm64']['x3' ])}")
    print(f"{cRegN} x4: {regFmt(mu,0,64,rNames['arm64']['x4' ])} {cRegN}  x5: {regFmt(mu,0,64,rNames['arm64']['x5' ])} {cRegN}  x6: {regFmt(mu,0,64,rNames['arm64']['x6' ])} {cRegN}  x7: {regFmt(mu,0,64,rNames['arm64']['x7' ])}")
    print(f"{cRegN} x8: {regFmt(mu,0,64,rNames['arm64']['x8' ])} {cRegN}  x9: {regFmt(mu,0,64,rNames['arm64']['x9' ])} {cRegN} x10: {regFmt(mu,0,64,rNames['arm64']['x10'])} {cRegN} x11: {regFmt(mu,0,64,rNames['arm64']['x11'])}")
    print(f"{cRegN}x12: {regFmt(mu,0,64,rNames['arm64']['x12'])} {cRegN} x13: {regFmt(mu,0,64,rNames['arm64']['x13'])} {cRegN} x14: {regFmt(mu,0,64,rNames['arm64']['x14'])} {cRegN} x15: {regFmt(mu,0,64,rNames['arm64']['x15'])}")
    print(f"{cRegN}x16: {regFmt(mu,0,64,rNames['arm64']['x16'])} {cRegN} x17: {regFmt(mu,0,64,rNames['arm64']['x17'])} {cRegN} x18: {regFmt(mu,0,64,rNames['arm64']['x18'])} {cRegN} x19: {regFmt(mu,0,64,rNames['arm64']['x19'])}")
    print(f"{cRegN}x20: {regFmt(mu,0,64,rNames['arm64']['x20'])} {cRegN} x21: {regFmt(mu,0,64,rNames['arm64']['x21'])} {cRegN} x22: {regFmt(mu,0,64,rNames['arm64']['x22'])} {cRegN} x23: {regFmt(mu,0,64,rNames['arm64']['x23'])}")
    print(f"{cRegN}x24: {regFmt(mu,0,64,rNames['arm64']['x24'])} {cRegN} x25: {regFmt(mu,0,64,rNames['arm64']['x25'])} {cRegN} x26: {regFmt(mu,0,64,rNames['arm64']['x26'])} {cRegN} x27: {regFmt(mu,0,64,rNames['arm64']['x27'])}")
    print(f"{cRegN}x28: {regFmt(mu,0,64,rNames['arm64']['x28'])} {cRegN} x29: {regFmt(mu,0,64,rNames['arm64']['x29'])} {cRegN} x30: {regFmt(mu,0,64,rNames['arm64']['x30'])} {cRegN}  sp: {regFmt(mu,2,64,rNames['arm64']['sp'] )}")
    print(f"{cRegN} pc: {regFmt(mu,1,64,rNames['arm64']['pc'] )} {cRegN}cpsr: {regFmt(mu,0,64,rNames['arm64']['cpsr'])}")
    print(cEnd,end="")
    if sConfig["arm64/neon"]:
        printRegs_NEON(mu, sConfig)

def printRegs_NEON(mu, sConfig):
    print(f"{cRegN} v0: {regFmt(mu,0,128,rNames['neon']['v0'] )} {cRegN}v16: {regFmt(mu,0,128,rNames['neon']['v16'])}")
    print(f"{cRegN} v1: {regFmt(mu,0,128,rNames['neon']['v1'] )} {cRegN}v17: {regFmt(mu,0,128,rNames['neon']['v17'])}")
    print(f"{cRegN} v2: {regFmt(mu,0,128,rNames['neon']['v2'] )} {cRegN}v18: {regFmt(mu,0,128,rNames['neon']['v18'])}")
    print(f"{cRegN} v3: {regFmt(mu,0,128,rNames['neon']['v3'] )} {cRegN}v19: {regFmt(mu,0,128,rNames['neon']['v19'])}")
    print(f"{cRegN} v4: {regFmt(mu,0,128,rNames['neon']['v4'] )} {cRegN}v20: {regFmt(mu,0,128,rNames['neon']['v20'])}")
    print(f"{cRegN} v5: {regFmt(mu,0,128,rNames['neon']['v5'] )} {cRegN}v21: {regFmt(mu,0,128,rNames['neon']['v21'])}")
    print(f"{cRegN} v6: {regFmt(mu,0,128,rNames['neon']['v6'] )} {cRegN}v22: {regFmt(mu,0,128,rNames['neon']['v22'])}")
    print(f"{cRegN} v7: {regFmt(mu,0,128,rNames['neon']['v7'] )} {cRegN}v23: {regFmt(mu,0,128,rNames['neon']['v23'])}")
    print(f"{cRegN} v8: {regFmt(mu,0,128,rNames['neon']['v8'] )} {cRegN}v24: {regFmt(mu,0,128,rNames['neon']['v24'])}")
    print(f"{cRegN} v9: {regFmt(mu,0,128,rNames['neon']['v9'] )} {cRegN}v25: {regFmt(mu,0,128,rNames['neon']['v25'])}")
    print(f"{cRegN}v10: {regFmt(mu,0,128,rNames['neon']['v10'])} {cRegN}v26: {regFmt(mu,0,128,rNames['neon']['v26'])}")
    print(f"{cRegN}v11: {regFmt(mu,0,128,rNames['neon']['v11'])} {cRegN}v27: {regFmt(mu,0,128,rNames['neon']['v27'])}")
    print(f"{cRegN}v12: {regFmt(mu,0,128,rNames['neon']['v12'])} {cRegN}v28: {regFmt(mu,0,128,rNames['neon']['v28'])}")
    print(f"{cRegN}v13: {regFmt(mu,0,128,rNames['neon']['v13'])} {cRegN}v29: {regFmt(mu,0,128,rNames['neon']['v29'])}")
    print(f"{cRegN}v14: {regFmt(mu,0,128,rNames['neon']['v14'])} {cRegN}v30: {regFmt(mu,0,128,rNames['neon']['v30'])}")
    print(f"{cRegN}v15: {regFmt(mu,0,128,rNames['neon']['v15'])} {cRegN}v31: {regFmt(mu,0,128,rNames['neon']['v31'])}")

def printRegs_x86(mu, sConfig):
    print(f"{cRegN}eax: {regFmt(mu,0,32,rNames['x86']['eax'])}")
    print(f"{cRegN}ecx: {regFmt(mu,0,32,rNames['x86']['ecx'])}")
    print(f"{cRegN}edx: {regFmt(mu,0,32,rNames['x86']['edx'])}")
    print(f"{cRegN}ebx: {regFmt(mu,0,32,rNames['x86']['ebx'])}")
    print(f"{cRegN}esp: {regFmt(mu,2,32,rNames['x86']['esp'])}")
    print(f"{cRegN}ebp: {regFmt(mu,0,32,rNames['x86']['ebp'])}")
    print(f"{cRegN}esi: {regFmt(mu,0,32,rNames['x86']['esi'])}")
    print(f"{cRegN}edi: {regFmt(mu,0,32,rNames['x86']['edi'])}")
    print(f"{cRegN}eip: {regFmt(mu,1,32,rNames['x86']['eip'])}")
    print(f"{cRegN}efl: {regFmt(mu,0,32,rNames['x86']['eflags'])}")
    print(cEnd,end="")
    if sConfig["x86/xmm"]:
        printRegs_XMM(mu, sConfig)

def printRegs_XMM(mu, sConfig):
    print(f"{cRegN} xmm0: {regFmt(mu,0,128,rNames['xmm']['xmm0'] )} {cRegN}xmm16: {regFmt(mu,0,128,rNames['xmm']['xmm16'])}")
    print(f"{cRegN} xmm1: {regFmt(mu,0,128,rNames['xmm']['xmm1'] )} {cRegN}xmm17: {regFmt(mu,0,128,rNames['xmm']['xmm17'])}")
    print(f"{cRegN} xmm2: {regFmt(mu,0,128,rNames['xmm']['xmm2'] )} {cRegN}xmm18: {regFmt(mu,0,128,rNames['xmm']['xmm18'])}")
    print(f"{cRegN} xmm3: {regFmt(mu,0,128,rNames['xmm']['xmm3'] )} {cRegN}xmm19: {regFmt(mu,0,128,rNames['xmm']['xmm19'])}")
    print(f"{cRegN} xmm4: {regFmt(mu,0,128,rNames['xmm']['xmm4'] )} {cRegN}xmm20: {regFmt(mu,0,128,rNames['xmm']['xmm20'])}")
    print(f"{cRegN} xmm5: {regFmt(mu,0,128,rNames['xmm']['xmm5'] )} {cRegN}xmm21: {regFmt(mu,0,128,rNames['xmm']['xmm21'])}")
    print(f"{cRegN} xmm6: {regFmt(mu,0,128,rNames['xmm']['xmm6'] )} {cRegN}xmm22: {regFmt(mu,0,128,rNames['xmm']['xmm22'])}")
    print(f"{cRegN} xmm7: {regFmt(mu,0,128,rNames['xmm']['xmm7'] )} {cRegN}xmm23: {regFmt(mu,0,128,rNames['xmm']['xmm23'])}")
    print(f"{cRegN} xmm8: {regFmt(mu,0,128,rNames['xmm']['xmm8'] )} {cRegN}xmm24: {regFmt(mu,0,128,rNames['xmm']['xmm24'])}")
    print(f"{cRegN} xmm9: {regFmt(mu,0,128,rNames['xmm']['xmm9'] )} {cRegN}xmm25: {regFmt(mu,0,128,rNames['xmm']['xmm25'])}")
    print(f"{cRegN}xmm10: {regFmt(mu,0,128,rNames['xmm']['xmm10'])} {cRegN}xmm26: {regFmt(mu,0,128,rNames['xmm']['xmm26'])}")
    print(f"{cRegN}xmm11: {regFmt(mu,0,128,rNames['xmm']['xmm11'])} {cRegN}xmm27: {regFmt(mu,0,128,rNames['xmm']['xmm27'])}")
    print(f"{cRegN}xmm12: {regFmt(mu,0,128,rNames['xmm']['xmm12'])} {cRegN}xmm28: {regFmt(mu,0,128,rNames['xmm']['xmm28'])}")
    print(f"{cRegN}xmm13: {regFmt(mu,0,128,rNames['xmm']['xmm13'])} {cRegN}xmm29: {regFmt(mu,0,128,rNames['xmm']['xmm29'])}")
    print(f"{cRegN}xmm14: {regFmt(mu,0,128,rNames['xmm']['xmm14'])} {cRegN}xmm30: {regFmt(mu,0,128,rNames['xmm']['xmm30'])}")
    print(f"{cRegN}xmm15: {regFmt(mu,0,128,rNames['xmm']['xmm15'])} {cRegN}xmm31: {regFmt(mu,0,128,rNames['xmm']['xmm31'])}")

def printRegs_x64(mu, sConfig):
    print(f"{cRegN}rax: {regFmt(mu,0,64,rNames['x64']['rax'])} {cRegN}rip: {regFmt(mu,1,64,rNames['x64']['rip'])} {cRegN}r11: {regFmt(mu,0,64,rNames['x64']['r11'])}")
    print(f"{cRegN}rbx: {regFmt(mu,0,64,rNames['x64']['rbx'])} {cRegN}rsp: {regFmt(mu,2,64,rNames['x64']['rsp'])} {cRegN}r12: {regFmt(mu,0,64,rNames['x64']['r12'])}")
    print(f"{cRegN}rcx: {regFmt(mu,0,64,rNames['x64']['rcx'])} {cRegN}rbp: {regFmt(mu,0,64,rNames['x64']['rbp'])} {cRegN}r13: {regFmt(mu,0,64,rNames['x64']['r13'])}")
    print(f"{cRegN}rdx: {regFmt(mu,0,64,rNames['x64']['rdx'])} {cRegN} r8: {regFmt(mu,0,64,rNames['x64']['r8'] )} {cRegN}r14: {regFmt(mu,0,64,rNames['x64']['r14'])}")
    print(f"{cRegN}rsi: {regFmt(mu,0,64,rNames['x64']['rsi'])} {cRegN} r9: {regFmt(mu,0,64,rNames['x64']['r9'] )} {cRegN}r15: {regFmt(mu,0,64,rNames['x64']['r15'])}")
    print(f"{cRegN}rdi: {regFmt(mu,0,64,rNames['x64']['rdi'])} {cRegN}r10: {regFmt(mu,0,64,rNames['x64']['r10'])} {cRegN}rfl: {regFmt(mu,0,64,rNames['x64']['rflags'])}")
    print(cEnd,end="")
    if sConfig["x86/xmm"]:
        printRegs_XMM(mu, sConfig)

archez = {
    "x64": {
        "emu": {
            "unicorn": {
                "arch": UC_ARCH_X86,
                "mode": UC_MODE_64,
                "stack_reg": UC_X86_REG_RSP,
                "ip_reg": UC_X86_REG_RIP,
            },
        },
        "asm": {
            "keystone": {
                "arch": KS_ARCH_X86,
                "mode": KS_MODE_64,
            },
        },
        "dis": {
            "capstone": {
                "arch": capstone.CS_ARCH_X86,
                "mode": capstone.CS_MODE_64,
            },
        },
        "funcs": {
            "reg_state": printRegs_x64,
        },
    },
    "x86": {
        "emu": {
            "unicorn": {
                "arch": UC_ARCH_X86,
                "mode": UC_MODE_32,
                "stack_reg": UC_X86_REG_ESP,
                "ip_reg": UC_X86_REG_EIP,
            },
        },
        "asm": {
            "keystone": {
                "arch": KS_ARCH_X86,
                "mode": KS_MODE_32,
            },
        },
        "dis": {
            "capstone": {
                "arch": capstone.CS_ARCH_X86,
                "mode": capstone.CS_MODE_32,
            },
        },
        "funcs": {
            "reg_state": printRegs_x86,
        },
    },
    "arm64": {
        "emu": {
            "unicorn": {
                "arch": UC_ARCH_ARM64,
                "mode": UC_MODE_ARM,
                "stack_reg": UC_ARM64_REG_SP,
                "ip_reg": UC_ARM64_REG_PC,
            },
        },
        "asm": {
            "keystone": {
                "arch": KS_ARCH_ARM64,
                "mode": KS_MODE_LITTLE_ENDIAN,
            },
        },
        "dis": {
            "capstone": {
                "arch": capstone.CS_ARCH_ARM64,
                "mode": capstone.CS_MODE_ARM,
            },
        },
        "funcs": {
            "reg_state": printRegs_arm64,
        },
    },
    "arm32": {
        "emu": {
            "unicorn": {
                "arch": UC_ARCH_ARM,
                "mode": UC_MODE_ARM,
                "stack_reg": UC_ARM_REG_SP,
                "ip_reg": UC_ARM_REG_PC,
            },
        },
        "asm": {
            "keystone": {
                "arch": KS_ARCH_ARM,
                "mode": KS_MODE_ARM,
            },
        },
        "dis": {
            "capstone": {
                "arch": capstone.CS_ARCH_ARM,
                "mode": capstone.CS_MODE_ARM,
            },
        },
        "funcs": {
            "reg_state": printRegs_arm32,
        },
    },
}

### Helper Functions ###########################################################
def configPrint(sConfig):
    print("Current Config Options")
    for cK, cV in sConfig.items():
        print(f"{cK} = {cV}")

# dHex - Dump Hex
# inBytes = byte array to dump
# baseAddr = the base address
def dHex(inBytes,baseAddr):
    offs = 0
    while offs < len(inBytes):
        bHex = ""
        bAsc = ""
        bChunk = inBytes[offs:offs+16]
        for b in bChunk:
            bAsc += chr(b) if chr(b).isprintable() and b < 0x7f else '.'
            bHex += "{:02x} ".format(b)
        sp = " "*(48-len(bHex))
        print("{:08x}: {}{} {}".format(baseAddr + offs, bHex, sp, bAsc))
        offs = offs + 16

# loadAsm - Load assembly listing from a file
def loadAsm(fname):
    with open(fname,"r") as f:
        outt = f.read().splitlines()
        f.close()
    out = []
    for oLine in outt:
        out.append(oLine.split(";")[0]) # Splits out comments
    print(f"Loaded {fname}")
    return out

# saveAsm - Save assembly listing to a file
def saveAsm(inCode, fname):
    out = "\n".join(inCode)
    out += "\n"
    with open(fname,"w") as f:
        f.write(out)
        f.close()
    print(f"Saved {fname}")

# exportBin - Export binary to a file
def exportBin(inCode, fileType, fArch, fname):
    if fileType == "bin":
        outBin = inCode
    elif fileType == "elf64":
        if fArch == "x64":
            eMach = b"\x3e\x00"
        elif fArch == "arm64":
            eMach = b"\xb7\x00"
        else:
            print("Unsupported Arch!")
            return
        b =  b"" # ELF64 Template based on https://n0.lol/test.asm
        b += b"\x7f\x45\x4c\x46\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"   # 00000000 .ELF............
        b += b"\x02\x00"+eMach+b"\x01\x00\x00\x00\x78\x00\x40\x00\x00\x00\x00\x00" # 00000010 ..>.....x.@.....
        b += b"\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"   # 00000020 @...............
        b += b"\x00\x00\x00\x00\x40\x00\x38\x00\x01\x00\x00\x00\x00\x00\x00\x00"   # 00000030 ....@.8.........
        b += b"\x01\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"   # 00000040 ................
        b += b"\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00"   # 00000050 ..@.......@.....
        b += b"\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00"   # 00000060 ................
        b += b"\x00\x02\x00\x00\x00\x00\x00\x00"                                   # 00000070 ........
        outBin = b
        outBin += inCode
    elif fileType == "pe32":
        if fArch == "x64":
            eMach = b"\x4c\x01"
        elif fArch == "x86":
            eMach = b"\x4c\x01"
        else:
            print("Unsupported Arch!")
            return
        b =  b"" # Tiny PE32 Template based on https://github.com/netspooky/kimagure/blob/main/pe32template.asm
        b += b"\x4d\x5a\x00\x01\x50\x45\x00\x00"+eMach+b"\x00\x00\x00\x00\x00\x00" # 00000000 MZ..PE..L.......
        b += b"\x00\x00\x00\x00\x00\x00\x00\x00\x60\x00\x03\x01\x0b\x01\x00\x00"   # 00000010 ........`.......
        b += b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7c\x00\x00\x00"   # 00000020 ............|...
        b += b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00\x04\x00\x00\x00"   # 00000030 ..........@.....
        b += b"\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00"   # 00000040 ................
        b += b"\x00\x00\x00\x00\x80\x00\x00\x00\x7c\x00\x00\x00\x00\x00\x00\x00"   # 00000050 ........|.......
        b += b"\x02\x00\x00\x04\x00\x00\x10\x00\x00\x10\x00\x00\x00\x00\x10\x00"   # 00000060 ................
        b += b"\x00"*12                                                            # 00000070 ............
        outBin = b
        outBin += inCode
    else:
        return
    with open(fname,"wb") as f:
        f.write(outBin)
        f.close()
    print(f"Exported code to {fname}")

def ksAssemble(ks_arch, ks_mode, CODE):
    try:
        ks = Ks(ks_arch, ks_mode)
        mc, num = ks.asm(CODE)
        return bytes(mc)
    except KsError as e:
        eChk = f"{e}"
        if "KS_ERR_ASM_SYMBOL_REDEFINED" in eChk:
            return # Returning because this will happen if a label is appended
        else:
            print("ERROR: %s" %e)
            return

def printListing(mu, asmInstructions, plan9=False):
    addr = sConfig["emu/baseaddr"]
    if len(asmInstructions) == 0:
        print("No instructions!")
        return
    asmString = "; ".join(asmInstructions)
    lineMax = 0
    for l in asmInstructions:
        lineMax = len(l) if len(l) > lineMax else lineMax
    asmAssembled = ksAssemble(mu.asm_arch, mu.asm_mode, "; ".join(asmInstructions))
    codeOffs = 0
    lineNum = 1
    empty = True
    # Predicting that in longer code with short jumps, this append trick will result in incorrect assembly if outside the range of a short jump
    for i in asmInstructions:
        asmStringLen = len(asmAssembled)
        tempAsmString = asmString +" ; " + i
        assembledAsm = ksAssemble(mu.asm_arch, mu.asm_mode, tempAsmString)
        if assembledAsm is not None:
            assembledAsmLen = len(assembledAsm) - asmStringLen # Disgusting hack to get the full length
        else:
            assembledAsmLen = 0
        asmBytes = asmAssembled[codeOffs:codeOffs+assembledAsmLen]
        spacing = " "*(lineMax - len(i))
        if plan9:
            if len(i) > 0:
                print(f"\tWORD $0x{asmBytes[::-1].hex()} // {i}")
                empty = False
            else:
                if not empty:
                    print("")
                empty = True
        else:
            print(f"{cLnNum}{lineNum:03d}{cEnd}{cLnPipe}│{cEnd} {cAsmList}{i}{cEnd} {spacing}{cComment}; {addr:04X}: {cBytes}{asmBytes.hex()}{cEnd}")
        addr = addr+assembledAsmLen
        codeOffs = codeOffs+assembledAsmLen
        lineNum = lineNum + 1

##### Main Class 
class scaremu:
    def __init__(self, inArch):
        if inArch in archez.keys():
            self.arch_name = inArch.lower()
            self.mu_arch   = archez[inArch]["emu"]["unicorn"]["arch"]
            self.mu_mode   = archez[inArch]["emu"]["unicorn"]["mode"]
            self.stack_reg = archez[inArch]["emu"]["unicorn"]["stack_reg"]
            self.ip_reg    = archez[inArch]["emu"]["unicorn"]["ip_reg"]
            self.asm_arch  = archez[inArch]["asm"]["keystone"]["arch"]
            self.asm_mode  = archez[inArch]["asm"]["keystone"]["mode"]
            self.dis_arch  = archez[inArch]["dis"]["capstone"]["arch"]
            self.dis_mode  = archez[inArch]["dis"]["capstone"]["mode"]
            self.base_addr = sConfig["emu/baseaddr"]
            self.stack_addr = sConfig["emu/stackaddr"]
            self.mu_memsize = sConfig["emu/memsize"]
            self.asm_code = [] # Holds the source code
            self.machine_code = b"" # The machine code
            self.mu_ctx = Uc(self.mu_arch, self.mu_mode)# This is the emulator object
            self.mu_ctx.mem_map(self.base_addr, self.mu_memsize)
            self.mu_ctx.reg_write(self.stack_reg, self.stack_addr) # Initialize Stack
            self.mu_state = "INIT" # The states are INIT, RUN, ERR
        else:
            print("Unsupported Arch")
            return
    def errPrint(self,eFunc, eMsg):
        print(f"{cErr}[[: {eFunc} Error :]]{cEnd}\n{eMsg}")
    def asm(self,asm_code):
        try:
            if self.arch_name in archez.keys():
                ks = Ks(self.asm_arch, self.asm_mode)
                self.asm_code = asm_code
                asmJoined = "; ".join(self.asm_code)
                mc, num = ks.asm(asmJoined)
                self.machine_code = bytes(mc)
                return 0
            else:
                print("Invalid Arch!")
                return 1
        except Exception as e:
            self.errPrint("asm",e)
            return 1
    def dis(self, memaddr, size):
        try:
            instructionList = []
            if self.arch_name in archez.keys():
                csArch = self.dis_arch
                csMode = self.dis_mode
            else:
                print("Invalid arch!")
                return instructionList
            scareDis = capstone.Cs(csArch, csMode)
            memout = self.mu_ctx.mem_read(memaddr, size)
            for insn in scareDis.disasm(memout, memaddr):
                instructionList.append(f"{insn.mnemonic} {insn.op_str}")
            return instructionList
        except Exception as e:
            self.errPrint("dis",e)
            return instructionList
    def run(self):
        runStatus = 1
        try:
            self.mu_ctx.emu_stop()
            if self.mu_state == "INIT":
                self.mu_ctx = Uc(self.mu_arch, self.mu_mode)
                self.mu_ctx.mem_map(self.base_addr, self.mu_memsize)
            self.mu_ctx.mem_write(self.base_addr, self.machine_code) # map the code
            self.mu_ctx.reg_write(self.stack_reg, self.stack_addr) # Initialize Stack
            eStart = self.mu_ctx.emu_start(self.base_addr, self.base_addr + len(self.machine_code)) # start emulator
            self.mu_state = "RUN"
            return self.mu_ctx.reg_read(self.ip_reg), 0
        except UcError as e:
            self.errPrint("run",e)
            return self.mu_ctx.reg_read(self.ip_reg), 1
    def stop(self):
        self.mu_ctx.emu_stop()
        self.mu_state = "INIT" # Switch back to initialized
    def printRegs(self):
        try:
            archez[self.arch_name]["funcs"]["reg_state"](self.mu_ctx, sConfig)
        except Exception as e:
            self.errPrint("printRegs",e)
        return
    def getReg(self, regname):
        arch = self.arch_name
        if not regname in rNames[arch]:
            if arch == "arm64":
                arch = "neon"
            elif arch == "x86" or arch == "x64":
                arch = "xmm"
        return rNames[arch][regname]
    def readReg(self, regname):
        try:
            reg_val = self.getReg(regname)
            if reg_val:
                reg_out = self.mu_ctx.reg_read(reg_val)
                return reg_out
        except Exception as e:
            self.errPrint("readReg",e)
    def writeReg(self, regname, v):
        try:
            reg_val = self.getReg(regname)
            if reg_val:
                reg_out = self.mu_ctx.reg_write(reg_val, v)
                return reg_out
        except Exception as e:
            self.errPrint("writeReg",e)
    def readMem(self, memaddr, size):
        try:
            memout = self.mu_ctx.mem_read(memaddr, size)
            dHex(memout, memaddr)
        except Exception as e:
            self.errPrint("readMem",e)
    def info(self):
        print(f"┌ {cInfo}   arch_name:{cEnd} {self.arch_name}")
        print(f"│ {cInfo}   base_addr:{cEnd} {self.base_addr:08x}")
        print(f"│ {cInfo}  stack_addr:{cEnd} {self.stack_addr:08x}")
        print(f"│ {cInfo}    mem_size:{cEnd} {self.mu_memsize:08x}")
        print(f"│ {cInfo}    asm_code:{cEnd} {self.asm_code}")
        print(f"│ {cInfo}machine_code:{cEnd} {self.machine_code.hex()}")
        print(f"└ {cInfo}    mu_state:{cEnd} {self.mu_state}")
