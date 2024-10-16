#!/usr/bin/env python
from __future__ import print_function
import time
import sys
import readline
import argparse
import numexpr
import traceback
from scarelib import *

parser = argparse.ArgumentParser(description="")
parser.add_argument('-a', dest='arch', help='Target architecture')
parser.add_argument('-c', dest='cpu', help='Target cpu')
parser.add_argument('-f', dest='inFile', help='File to read')
parser.add_argument('--base', type=lambda x: parseInt(x), dest='baseaddr', help='Base Address (default: 0x400000)')
parser.add_argument('--stack', type=lambda x: parseInt(x), dest='stackaddr', help='Stack Address (default: 0x401000)')
parser.add_argument('--memsize', dest='memsize', help='Emulator Memory Size (default: 0x800000 [8MB])')

## Commands
cmdQuit = ["/exit", "/x", "/quit", "/q"]
cmdHelp = ["/", "/help", "/?", "/h"]
cmdConf = ["/config", "/c"]
cmdPList= ["/list", "/l"]

def parseInt(x):
    return int(numexpr.evaluate(x).item())

# parseCmd
# Commands must start with / to be parsed
# If 0 is returned, the main command loop will not try to assemble the input
# If 1 is returned, then the main command loop should try to assemble the input
# If 2 is returned, the main command loop should not append the current command and just assemble and run
# If 3 is returned, reinitialize the scaremu
def parseCmd(cmd, smu):
    shouldAssemble = 1
    if len(cmd) > 0:
      if cmd[0] == "/":
        shouldAssemble = 0
        cmdList = cmd.split()
        cmdListLen = len(cmdList)

        if cmdList[0] in cmdQuit:
            sys.exit()

        if cmdList[0] in cmdHelp:
            print(helpfile)

        if cmdList[0] in cmdConf:
            if cmdListLen == 3 or cmdListLen == 4:
                try:
                    cfgOptName = cmdList[1]
                    cfgOptVal = cmdList[2]
                    cfgOptExtra = cmdList[3] if cmdListLen == 4 else ""
                    if cfgOptName in sConfig.keys():
                        third = ("/"+cfgOptExtra) if cfgOptExtra != "" else ""
                        print(f"{cfgOptName}->{cfgOptVal}{third}")
                        # TODO: Keep better track of config option types
                        if cfgOptName == "emu/arch":
                            okArch = cfgOptVal in archez.keys()
                            if okArch:
                                arch = archez[cfgOptVal]
                                if cfgOptExtra in arch["cpus"].keys():
                                    sConfig[cfgOptName] = cfgOptVal
                                    sConfig["emu/cpu"] = cfgOptExtra
                                else:
                                    print(f"Invalid cpu! Supported cpus: {arch["cpus"].keys()}")
                            else:
                                print(f"Invalid arch! Supported arches: {archez.keys()}")
                        else:
                            sConfig[cfgOptName] = parseInt(cfgOptVal)
                    else:
                        print("Invalid config opt name!")
                except Exception as e:
                    print(f"Error in /config:")
                    print(traceback.format_exc())
            elif cmdListLen == 2:
                try:
                    cfgOptName = cmdList[1]
                    if cfgOptName in sConfig.keys():
                        print(f"{cfgOptName} = {sConfig[cfgOptName]}")
                except Exception as e:
                    print(f"Error in /config:")
                    print(traceback.format_exc())
            else:
                configPrint(sConfig)

        if cmdList[0] == "/info":
            if smu:
                smu.info()
            else:
                print("No emulator running!")

        if cmdList[0] == "/regs":
            if smu:
                smu.printRegs()
            else:
                print("No emulator running!")

        if cmdList[0] == "/back":
            backAmount = parseInt(cmdList[1])
            if backAmount <= len(smu.asm_code):
                smu.asm_code = smu.asm_code[:-backAmount]
                print(f"Moved back {backAmount} lines to line {len(smu.asm_code)}")
                shouldAssemble = 2 # Reassemble and run
            else:
                print(f"Too far back! You're currently on line {len(smu.asm_code)}")

        if cmdList[0] == "/load":
            if cmdListLen > 1:
                smu.asm_code = loadAsm(cmdList[1], lambda c: parseCmd(c, smu))
                currentAddr = sConfig["emu/baseaddr"]
            else:
                print("Please specify a filename!")

        if cmdList[0] == "/save":
            if cmdListLen > 1:
                saveAsm(smu.asm_code, cmdList[1])
            else:
                print("Please specify a filename!")

        if cmdList[0] == "/run":
            shouldAssemble = 2 # Reassemble and run

        if cmdList[0] == "/reset":
            shouldAssemble = 3 # Reinitialize 

        if cmdList[0] in cmdPList:
            printListing(smu, smu.asm_code, plan9=("plan9" in cmdList))

        if cmdList[0] == "/read":
            if cmdListLen >= 3 and cmdListLen <= 4:
                try:
                    memout = 0
                    baseAddr = 0
                    if cmdList[1][0] == "$":
                        regTarget = cmdList[1].split("$")[1]
                        regValue = smu.readReg(regTarget)
                        if regValue is not None:
                            memout = smu.mu_ctx.mem_read(regValue, parseInt(cmdList[2]))
                            baseAddr = regValue
                    else:
                        baseAddr = parseInt(cmdList[1])
                        memout = smu.mu_ctx.mem_read(baseAddr, parseInt(cmdList[2]))
                    if memout:
                        if cmdListLen > 3:
                            with open(cmdList[3], "wb") as f:
                                f.truncate()
                                f.write(memout)
                        else:
                            dHex(memout, baseAddr)
                    else:
                        print("Usage: /read {0xaddress|$register} size")
                except Exception as e:
                    print(e)
                    print("Usage: /read {0xaddress|$register} size")
            else:
                print("Usage: /read {0xaddress|$register} size")

        if cmdList[0] == "/write":
            if cmdListLen == 3:
                try:
                    if cmdList[2][0] == '.':
                        with open(cmdList[2], "rb") as f:
                            data = f.read(-1)
                            print(f"{cmdList[2]}: {len(data)} bytes")
                    else:
                        data = bytes.fromhex(cmdList[2])
                    if cmdList[1][0] == "$":
                        regTarget = cmdList[1].split("$")[1]
                        regValue = smu.readReg(regTarget)
                        if regValue is not None:
                            smu.mu_ctx.mem_write(regValue, data)
                    else:
                        memout = smu.mu_ctx.mem_write(parseInt(cmdList[1]), data)
                except Exception as e:
                    print(e)
                    print("Usage: /write {0xaddress|$register} hexdata")
            else:
                print("Usage: /write {0xaddress|$register} hexdata")

        if cmdList[0] == "/set":
            if cmdListLen == 3:
                try:
                    regTarget = cmdList[1]
                    value = parseInt(cmdList[2])
                    smu.writeReg(regTarget, value)
                except Exception as e:
                    print(e)
                    print("Usage: /set register value")
            else:
                print("Usage: /set register value")

        if cmdList[0] == "/get":
            if cmdListLen >= 2:
                try:
                    for regTarget in cmdList[1:]:
                        value = smu.readReg(regTarget)
                        print(f"{cRegN} {regTarget}: {value:032x}")
                except Exception as e:
                    print(e)
                    print("Usage: /get register [register... ]")
            else:
                print("Usage: /get register [register... ]")

        if cmdList[0] == "/dis":
            try:
                if cmdListLen == 3:
                    if cmdList[1][0:2] == "0x":
                        instructions4dis = smu.dis(parseInt(cmdList[1]), parseInt(cmdList[2]))
                        printListing(smu, instructions4dis)
                    elif cmdList[1][0] == "$":
                        regTarget = cmdList[1].split("$")[1]
                        regValue = smu.readReg(regTarget)
                        if regValue is not None:
                            instructions4dis = smu.dis(regValue, parseInt(cmdList[2]))
                            printListing(smu, instructions4dis)
                    else:
                        print("Usage: /dis {0xaddress|$register} size")
                else:
                    print("Usage: /dis {0xaddress|$register} size")
            except Exception as e:
                print(e)
                print("Usage: /dis {0xaddress|$register} size")

        if cmdList[0] == "/export":
            try:
                if cmdListLen == 3:
                    fArch = smu.arch_name
                    if cmdList[1] == "bin":
                        mcLen = len(smu.machine_code)
                        if mcLen > 0:
                            print(f"Exporting {mcLen} bytes of code as raw binary")
                            exportBin(smu.machine_code, "bin", fArch, cmdList[2])
                        else:
                            print("No machine code to export!")
                    elif cmdList[1] == "elf64":
                        mcLen = len(smu.machine_code)
                        if mcLen > 0:
                            print(f"Exporting {mcLen} bytes of code as ELF64")
                            exportBin(smu.machine_code, "elf64", fArch, cmdList[2])
                        else:
                            print("No machine code to export!")
                    else:
                        print("Invalid binary type!")
                else:
                    print("Usage: /export type filename")
            except Exception as e:
                print(f"Export Error: {e}")
    else:
        shouldAssemble = 0 # Don't do anything if there's no input

    return shouldAssemble

if __name__ == '__main__':
    args = parser.parse_args()
    print("Type / for help\n")
    inFile = args.inFile if args.inFile else ""
    currentArch = args.arch.lower() if args.arch else "NoArch"
    currentCpu = args.cpu.lower() if args.cpu else ""
    if args.stackaddr:
        sConfig["emu/stackaddr"] = args.stackaddr
    if args.baseaddr:
        sConfig["emu/baseaddr"] = args.baseaddr
    if args.memsize:
        sConfig["emu/memsize"] = args.memsize   
    if currentArch == "NoArch":
        print(f"Please select an architecture! Use `/c emu/arch ARCH`.\nSupported arches: {archez.keys()}")
        smu = False
        currentAddr = sConfig["emu/baseaddr"]
    else:
        sConfig["emu/arch"] = currentArch
        sConfig["emu/cpu"] = currentCpu
        smu = scaremu(currentArch, currentCpu)
        currentAddr = sConfig["emu/baseaddr"]
        if inFile:
            smu.asm_code = loadAsm(inFile, lambda c: parseCmd(c, smu))
    printSplash()
    while True:
        try:
            cmd = input(f"[{cArchP}{currentArch}]{cIP}{currentAddr:02x}{cEnd}> ")
            try:
                shouldAsm = parseCmd(cmd, smu)
            except:
                continue
            if    (((smu == False) and (sConfig["emu/arch"] != "NoArch")) or
                   sConfig["emu/arch"] != currentArch or
                   shouldAsm == 3):
                currentArch = sConfig["emu/arch"]
                currentCpu = sConfig["emu/cpu"]
                currentAddr = sConfig["emu/baseaddr"]
                smu = scaremu(currentArch, currentCpu)
            if smu != False and shouldAsm:
                if shouldAsm == 1:
                    smu.asm_code.append(cmd)
                if len(smu.asm_code) > 0:
                    asmStatus = smu.asm(smu.asm_code)
                    if asmStatus == 0:
                        currentAddr, runStatus = smu.run()
                        if runStatus == 0:
                            smu.printRegs()
                        else:
                            print("run() returned a non-zero value")
                    else:
                        smu.asm_code.pop() # Gets rid of the last line of assembly
                else:
                    currentAddr = sConfig["emu/baseaddr"]
        except EOFError:
            break
