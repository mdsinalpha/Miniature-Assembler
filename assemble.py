"""
    this module is a driver code for testing Miniature Assembler module
    imports Assembler from core.py
    for more details about project read README.md
"""

from sys import argv
from core import Assembler

if argv[0] != "assemble.py":
    exit(0)

try:
    # read assembly code from input :
    asm = open(argv[1], "r").readlines()

    # pass a list of code lines through Assembler class
    assemble = Assembler(asm)
    # go and assemble !
    open(argv[2], "w").writelines(assemble.go())
    print("Assembled successfully!")

except ValueError as error:
    open(argv[2], "w").write("# " + str(error))
    print(error)

