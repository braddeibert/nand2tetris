"""
Assembler for nand2tetris course, translates Hack assembly code into machine language (binary)
CSCI361 at University of Montana, Spring 2020

author: @braddeibert
"""

import os
import sys

#dictionary to track RAM/ROM addresses
symbols = {
         "R0" :  0,
         "R1" :  1,
         "R2" :  2,
         "R3" :  3,
         "R4" :  4,
         "R5" :  5,
         "R6" :  6,
         "R7" :  7,
         "R8" :  8,
         "R9" :  9,
         "R10" :  10,
         "R11" :  11,
         "R12" :  12,
         "R13" :  13,
         "R14" :  14,
         "R15" :  15,
         "SCREEN" : 16384,
         "KBD" :  24576,
         "SP" : 0,
         "LCL" :  1,
         "ARG" : 2,
         "THIS" : 3,
         "THAT" : 4
}

#empty string to write output to
output = ''

#remove comments, whitespace from code
def Line2Command(l):
    list = l.split('//')
    l = list[0]
    l = l.replace(" ", "")
    return l.strip()

def dest2bin(mnemonic):
    dest = {
        "" : "000",
        "M" : "001",
        "D" : "010",
        "MD" : "011",
        "A" : "100",
        "AM" : "101",
        "AD" : "110", 
        "AMD" : "111"
    }

    return dest[mnemonic]

def comp2bin(mnemonic):
    comp = {
        "0" : "101010",
        "1" : "111111",
        "-1" : "111010",
        "D" : "001100",
        "A" : "110000",
        "M" : "110000",
        "!D" : "001101", 
        "!A" : "110001",
        "!M" : "110001",
        "-D" : "001111",
        "-A" : "110011",
        "-M" : "110011",
        "D+1" : "011111",
        "1+D" : "011111",
        "A+1" : "110111",
        "1+A" : "110111",
        "M+1" : "110111",
        "1+M" : "110111",
        "D-1" : "001110",
        "A-1" : "110010",
        "M-1" : "110010",
        "D+A" : "000010",
        "A+D" : "000010",
        "D+M" : "000010",
        "M+D" : "000010",
        "D-A" : "010011",
        "D-M" : "010011",
        "A-D" : "000111",
        "M-D" : "000111",
        "D&A" : "000000",
        "A&D" : "000000",
        "D&M" : "000000",
        "M&D" : "000000",
        "D|A" : "010101",
        "A|D" : "010101",
        "D|M" : "010101",
        "M|D" : "010101"
    }

    if mnemonic.find('M') >= 0:
        return "1" + comp[mnemonic]
    else:
        return "0" + comp[mnemonic]

def jump2bin(mnemonic):
    jump = {
        "" : "000",
        "JGT" : "001",
        "JEQ" : "010",
        "JGE" : "011",
        "JLT" : "100",
        "JNE" : "101",
        "JLE" : "110", 
        "JMP" : "111"
    }
    
    return jump[mnemonic]

def commandType(command):
    if command[0] == '(':
        return 'L_COMMAND'

    elif command[0] == '@':
        return 'A_COMMAND'

    else: return 'C_COMMAND'

def getSymbol(command):
    if commandType(command) == 'L_COMMAND':
        command = command[1:len(command) - 1]
        return command
    elif commandType(command) == 'A_COMMAND':
        command = command[1:len(command)]
        return command
    
def getDest(command):
    if command.find('=') > 0:
        list = command.split('=')
        return list[0]
    
    return ""

def getComp(command):
    if command.find('=') > 0:
        list = command.split('=')
        command = list[1]
    
    if command.find(';') > 0:
        list = command.split(';')
        command = list[0]

    return command


def getJump(command):
    if command.find(';') > 0:
        list = command.split(';')
        command = list[1]
        return command
    
    return ""


#function to parse each line in file and store labels in RAM
def Pass1(f):
    lineCount = -1

    for line in f:
        command = Line2Command(line)
        if len(command) > 0:
            lineCount += 1

            if commandType(command) == 'L_COMMAND':
                command = getSymbol(command)
                
                symbols[command] = lineCount
                lineCount -= 1


#function for second file parse, translates lines to binary
def Pass2(f):
    nextRAM_addr = 16

    for line in f:
        global output 

        command = Line2Command(line)
        if len(command) > 0:
            if commandType(command) == 'A_COMMAND':
                command = getSymbol(command)

                if (command in symbols):
                    num = symbols[command]

                    binary = format(num, 'b')
                    binary = binary.zfill(16)

                    output = output + binary + '\n'

                else:
                    if command.isdigit():
                        command = int(command)
                        binary = format(command, 'b')
                        binary = binary.zfill(16)

                        output = output + binary + '\n'
                        continue

                    symbols[command] = nextRAM_addr
                    
                    binary = format(nextRAM_addr, 'b')
                    binary = binary.zfill(16)

                    output = output + binary + '\n'

                    nextRAM_addr += 1


            elif commandType(command) == 'C_COMMAND':
                binary = ""

                comp = comp2bin(getComp(command))
                binary = binary + comp

                dest = dest2bin(getDest(command))
                binary = binary + dest

                jump = jump2bin(getJump(command))
                binary = binary + jump

                binary = binary.zfill(13)
                output = output + '111' + binary + '\n'
        
            
#check an .asm arg is passed
if len(sys.argv) != 2:
    print ("Usage: HackAssembler.py filename.asm")
    sys.exit(-1)
    
filename = sys.argv[1].strip()

with open(filename) as file:
    Pass1(file)

with open(filename) as file:
    Pass2(file)

#writing binary to file (.hack)
writename = filename[0:len(filename) - 4] + ".hack"
out = open(writename, "w+")
out.write(output)
out.close()