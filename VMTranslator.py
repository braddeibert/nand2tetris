"""
VM Translator for nand2tetris course, translates vm files to hack assembly language
CSCI361 at The University of Montana, Spring 2020

author: @braddeibert
"""

import os
import glob
import sys

output = ''                                    #global string to concatenate assembly code to as it is translated, later to be written to an output .asm file

labelCount = 0                                 #used for creating unique labels
pushD = '@SP, A=M, M=D, @SP, M=M+1, '          #assembly to push D register contents to vm stack
popToD = '@SP, AM=M-1, D=M, '                  #assembly to pop top of vm stack to D register

#check for args
if len(sys.argv) != 2:
    print ("Usage: VMTranslator.py filename.vm")
    sys.exit(-1)


#help functions below for memory segments
def _getSTATIC(type, val):
    global name
    asm = name.split('/')
    asm = asm[len(asm) - 1]

    staticLabel = asm + '.%s' % val

    if type == 'push':
        return '@%s, D=M, ' % staticLabel + pushD 
    else:
        return popToD + '@%s, M=D, ' % staticLabel


def _getPTR(type, val):
    if val == '0':    #THIS
        if type == 'push':
            return '@THIS, D=M, ' + pushD
        else:
            return popToD + '@THIS, M=D, '

    else:           #THAT
        if type == 'push':
            return '@THAT, D=M, ' + pushD
        else:
            return popToD + '@THAT, M=D, '


def _getTMP(type, val):
    if type == 'push':
        return '@5, D=A, @%s, A=D+A, D=M, ' % val + pushD 
    else:
        return '@5, D=A, @%s, D=D+A, @temp, M=D, ' % val + popToD + '@temp, A=M, M=D, ' 


def _getLCL(type, val):
    if type == 'push':
        return '@LCL, D=M, @%s, A=D+A, D=M, ' % val + pushD 
    else:
        return '@LCL, D=M, @%s, D=D+A, @temp, M=D, ' % val + popToD + '@temp, A=M, M=D, ' 


def _getARG(type, val):
    if type == 'push':
        return '@ARG, D=M, @%s, A=D+A, D=M, ' % val + pushD 
    else:
        return '@ARG, D=M, @%s, D=D+A, @temp, M=D, ' % val + popToD + '@temp, A=M, M=D, ' 


def _getTHIS(type, val):
    if type == 'push':
        return '@THIS, D=M, @%s, A=D+A, D=M, ' % val + pushD 
    else:
        return '@THIS, D=M, @%s, D=D+A, @temp, M=D, ' % val + popToD + '@temp, A=M, M=D, ' 


def _getTHAT(type, val):
    if type == 'push':
        return '@THAT, D=M, @%s, A=D+A, D=M, ' % val + pushD 
    else:
        return '@THAT, D=M, @%s, D=D+A, @temp, M=D, ' % val + popToD + '@temp, A=M, M=D, ' 


#help functions/variables below for handling asm/vm functions
def _return():
    commands = ''

    #saves location of LCL to R15 for restoring the stack (below)
    commands += '@LCL, D=M, @R15, M=D, @5, A=D-A, D=M, @ret, M=D, ' 

    #place the return value atop the stack & reposition the stack pointer
    commands += popToD + '@ARG, A=M, M=D, D=A, @SP, M=D+1, '

    #comands below restore the caller's stack
    commands += '@R15, A=M-1, D=M, @THAT, M=D, '
    commands += '@R15, D=M, @2, A=D-A, D=M, @THIS, M=D, '
    commands += '@R15, D=M, @3, A=D-A, D=M, @ARG, M=D, '
    commands += '@R15, D=M, @4, A=D-A, D=M, @LCL, M=D, '

    #jumps back to execution of the caller
    commands += '@ret, A=M, 0;JMP, '

    return commands


def _function(name, numLocals):
    commands = '(%s), D=0, ' % name
    
    #initialize function local variables to 0
    for i in range(int(numLocals)):
        commands += pushD

    return commands


callCount = 0
def _call(funcName, numArgs):
    commands = ''

    #create a return address label
    global callCount
    funcLabel = funcName + '$ret.' + str(callCount)
    callCount += 1

    #save the caller's frame & return address
    commands += '@%s, D=A, ' % funcLabel + pushD + '@LCL, D=M, ' + pushD + '@ARG, D=M, ' + pushD + '@THIS, D=M, ' + pushD + '@THAT, D=M, ' + pushD

    #set args for called function
    commands += '@SP, D=M, @5, D=D-A, @%s, D=D-A, @ARG, M=D, ' % numArgs

    #repositions lcl
    commands += '@SP, D=M, @LCL, M=D, '

    #transfers control to called function
    commands += '@%s, 0;JMP, ' % funcName

    #return address label
    commands += '(%s), ' % funcLabel

    return commands


#vm/assembly code entries for stack arithmetic operations
stack_arith = {'add': popToD + 'A=A-1, M=D+M, ',
                'sub': popToD + 'A=A-1, M=M-D, ',
                'and': popToD + 'A=A-1, M=M&D, ',
                'or': popToD + 'A=A-1, M=M|D, ',
                'neg': '@SP, A=M-1, M=-M, ',
                'not': '@SP, A=M-1, M=!M, ',
                'gt': popToD + 'A=A-1, D=M-D, M=0, @%s, D;JGT, @%s, 0;JMP, (%s), @SP, A=M-1, M=!M, (%s), ',
                'lt': popToD + 'A=A-1, D=M-D, M=0, @%s, D;JLT, @%s, 0;JMP, (%s), @SP, A=M-1, M=!M, (%s), ',
                'eq': popToD + 'A=A-1, D=M-D, M=0, @%s, D;JEQ, @%s, 0;JMP, (%s), @SP, A=M-1, M=!M, (%s), '}

#vm/assembly code entries for managing memory segments
memory_segs = {'constant':'@%s, D=A, ' + pushD,
                'static': _getSTATIC,
                'pointer': _getPTR,
                'temp': _getTMP,
                'local': _getLCL,
                'argument': _getARG,
                'this': _getTHIS,
                'that': _getTHAT }

#vm/assembly code entries for handling branching
branching = {
    'goto': '@%s, 0;JMP, ',
    'if-goto': popToD + '@%s, D;JNE, ',
    'label': '(%s), ' }

#vm/assembly code entries for function calls 
functions = {
    'call': _call,
    'function': _function,
    'return': _return }

#assembly code to initialize the virtual machine
def getInit(sysinit = True):
    global output

    #initialize SP to 256
    output += '@256, D=A, @SP, M=D, '

    if sysinit:
        #initialize LCL, ARG, THIS, THAT to -1
        output += 'A=A+1, M=-1, A=A+1, M=-1, A=A+1, M=-1, A=A+1, M=-1, '

        #call sys.init
        output += _call('Sys.init', 0) 
        
        #place execution into an infinite loop
        halt = 'INF_LOOP'
        output += '@%s, (%s), 0;JMP, ' % (halt, halt)


#remove comments and whitespace from code
def Line2Command(l):
    return l[:l.find('//')].strip()

#translate a vm command to assembly
def Translate(command):
    global pushD, popToD, labelCount

    #breaks vm command into keyword components
    command = command.split(' ')
            
    #return command
    if command[0] == 'return':
        return functions[command[0]]()

    #stack arithmetic commands
    elif (len(command) == 1):

        #stack test commands
        if command[0] == 'gt' or command[0] == 'lt' or command[0] == 'eq':
            jump1 = 'L' + str(labelCount)
            jump2 = 'L' + str(labelCount + 1)

            labelCount += 2
            return (stack_arith[command[0]] % (jump1, jump2, jump1, jump2))

        return stack_arith[command[0]]
    
    #branching commands
    elif len(command) == 2:
        return (branching[command[0]] % command[1])

    #memory segment commands
    elif (command[0] == 'push' or command[0] == 'pop'):
        if (command[1] == 'constant'):
            return memory_segs[command[1]] % command[2]

        return (memory_segs[command[1]](command[0], command[2]))

    #function & call commands
    else:
        return (functions[command[0]](command[1], command[2]))


#parse the input file
def ParseFile(f):
    global output

    for line in f:
        command = Line2Command(line)

        if len(command) > 0: 
            output += Translate(command)


source = sys.argv[1].strip()
filename = source

#check for directory argument
if os.path.isdir(source):
    vmFiles = glob.glob(source+"/*.vm")
    writename = filename + '/' + filename + '.asm'

    getInit()
    
    for filename in vmFiles:
        name = filename

        with open(filename) as file:
            ParseFile(file)

#single vm file argument
else:
    filename = source
    name = filename[:len(filename) - 3]
    writename = name + '.asm'

    getInit(sysinit=False)

    with open(filename) as file:
        ParseFile(file)


#write assembly to file (.asm)
out = open(writename, "w+")
out.write(output.replace(', ', '\n'))        #write each assembly line on newline
out.close()
