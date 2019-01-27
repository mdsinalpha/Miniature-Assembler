import re


class Instruction:
    """
    An abstract class for holding instructions of an assembly code
    """
    # todo 1-define valid commands dictionary
    commands = {"R": ("add", "sub", "slt", "or", "and"),
                "I1": ("addi", "ori", "slti", "lw", "sw", "beq"),
                "I2": "lui",
                "I3": "jalr",
                "J": "j",
                "H": "halt"}

    def __init__(self, command: str, rest: str, line_index: int=None):
        """
        Constructor for Instruction class
        """
        self._command = command.strip()
        self._type = None

        # Determine what type this command is:
        for key, value in self.commands.items():
            if isinstance(value, str):
                if value == command:
                    self._type = key
                    break
            else:
                for c_value in value:
                    if c_value == self._command:
                        self._type = key
                        break

        if self._type is None:
            error = "No such command found : %s" % command
            if line_index is not None:
                error += " on line %d " % line_index
            error += "."
            raise ValueError(error)

        self._rest = rest
        # Line index to show which line error has occurred:
        self._line_index = line_index
        # Field is the final binary code(result):
        self.field = list("0" * 32)

    @property
    def command(self):
        return self._command

    @property
    def type(self):
        return self._type

    @property
    def rest(self):
        return self._rest

    @property
    def line_index(self):
        return self._line_index


class RType(Instruction):

    # todo 1-define (rest) regex
    regex = "([0-9]+),([0-9]+),([0-9]+)"

    # todo 2-define field dictionaries
    op_code = {"add":  "0000",
               "sub":  "0001",
               "slt":  "0010",
               "or":   "0011",
               "and": "0100"}

    def __init__(self, instruction: Instruction):
        """
        Constructor for RType Instruction class
        """
        super().__init__(instruction.command, instruction.rest, instruction.line_index)

        # Extracting 3 operand register numbers:
        extract = re.findall(self.regex, self.rest)
        if len(extract) == 0:
            error = "Wrong register numbers"
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)
        extract = extract[0]
        destination, source, target = map(int, (extract[0], extract[1], extract[2]))

        # Handling operand register number errors:
        error = ""
        if destination == 0:
            error += "Destination register can not be zero"
        elif destination > 15:
            if error != "":
                error += ", "
            error += "Destination register must be less than 16"
        if source > 15:
            if error != "":
                error += ", "
            error += "Source register must be less than 16"
        if target > 15:
            if error != "":
                error += ", "
            error += "Target register must be less than 16"
        if error != "":
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)

        # Setting operand register numbers up:
        self.destination, self.source, self.target = destination, source, target

    # todo 3-fill machine code
    @property
    def machine_code(self):
        self.field[4:8] = self.op_code[self.command]
        self.field[8:12] = "{0:04b}".format(self.source)
        self.field[12:16] = "{0:04b}".format(self.target)
        self.field[16:20] = "{0:04b}".format(self.destination)
        return ''.join(self.field)


class IType1(Instruction):

    # todo 1-define (rest) regex
    regex = "([0-9]+),([0-9]+),([-\w]+)"

    # todo 2-define field dictionaries
    op_code = {"addi": "0101",
               "ori":  "0111",
               "slti": "0110",
               "lw":   "1001",
               "sw":   "1010",
               "beq":  "1011"}

    def __init__(self, instruction: Instruction, table):
        """
        Constructor for IType1 Instruction class
        :param: table: a dictionary that has labels with their values stored
        """
        super().__init__(instruction.command, instruction.rest, instruction.line_index)

        # Extracting 2 operand register numbers + immediate/offset field:
        extract = re.findall(self.regex, self.rest)
        self.table = table
        if len(extract) == 0:
            error = "Wrong register numbers or immediate(offset) value"
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)
        extract = extract[0]
        destination, source = map(int, (extract[0], extract[1]))
        value = extract[2]

        # Handling operand register number errors:
        error = ""
        if destination == 0 and self.command != "beq":
            error += "Destination register can not be zero"
        elif destination > 15:
            if error != "":
                error += ", "
            error += "Destination register must be lest than 16"
        if source > 15:
            if error != "":
                error += ", "
            error += "Source register must be less than 16"
        if error != "":
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)

        # Setting operand register numbers + immediate/offset value up:
        self.destination, self.source, self.value = destination, source, value

    # todo 3-fill machine code
    @property
    def machine_code(self):
        self.field[4:8] = self.op_code[self.command]
        self.field[8:12] = "{0:04b}".format(self.source)
        self.field[12:16] = "{0:04b}".format(self.destination)

        # Handling immediate/offset field set-up with errors:
        if self.value.lstrip("-").isdecimal():
            self.value = int(self.value)
            if self.value >= 2 ** 16:
                error = "Immediate(offset) value is too large : %d" % self.value
                if self.line_index is not None:
                    error += " on line : %d " % self.line_index
                error += "."
                raise ValueError(error)
            if self.value >= 0:
                self.field[16:32] = "{0:016b}".format(self.value)
            # Two's complement if negative:
            else:
                self.field[16:32] = "{0:016b}".format(2 ** 16 + self.value)
        else:
            # If immediate field is a directive we should go find the value inside table
            if self.value not in self.table:
                error = "Undefined label : %s" % self.value
                if self.line_index is not None:
                    error += " on line : %d" % self.line_index
                error += "."
                raise ValueError(error)
            # Calculate relative branch target address:
            if self.command == "beq":
                target = self.table[self.value] - self.line_index - 1
                if target >= 0:
                    self.field[16:32] = "{0:016b}".format(target)
                # Two's complement if negative:
                else:
                    self.field[16:32] = "{0:016b}".format(2 ** 16 + target)
            elif self.table[self.value] >= 0:
                self.field[16:32] = "{0:016b}".format(self.table[self.value])
            # Two's complement if negative:
            else:
                self.field[16:32] = "{0:016b}".format(2 ** 16 + self.table[self.value])

        return ''.join(self.field)


class IType2(Instruction):

    # todo 1-define regex
    regex = "([0-9]+),([-\w]+)"

    # todo 2-define field dictionaries
    op_code = {"lui": "1000"}

    def __init__(self, instruction: Instruction, table):
        """
        Constructor for IType2 Instruction class
        :param: table: a dictionary that has labels with their values stored
        """
        super().__init__(instruction.command, instruction.rest, instruction.line_index)

        # Extracting 1 operand register number + immediate/offset field:
        extract = re.findall(self.regex, self.rest)
        self.table = table
        if len(extract) == 0:
            error = "Wrong register numbers or immediate(offset) value"
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)
        extract = extract[0]
        destination = int(extract[0])
        value = extract[1]

        # Handling operand register number errors:
        error = ""
        if destination == 0:
            error += "Destination register can not be zero"
        elif destination > 15:
            if error != "":
                error += ", "
            error += "Destination register must be less than 16"
        if error != "":
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)

        # Setting operand register number + immediate/offset value up:
        self.destination, self.value = destination, value

    # todo 3-fill machine code
    @property
    def machine_code(self):
        self.field[4:8] = self.op_code[self.command]
        self.field[12:16] = "{0:04b}".format(self.destination)

        # Handling immediate/offset field set-up with errors:
        if self.value.lstrip("-").isdecimal():
            self.value = int(self.value)
            if self.value >= 2 ** 16:
                error = "Immediate(offset) value is too large : %d" % self.value
                if self.line_index is not None:
                    error += " on line : %d " % self.line_index
                error += "."
                raise ValueError(error)
            if self.value >= 0:
                self.field[16:32] = "{0:016b}".format(self.value)
            # Two's complement if negative:
            else:
                self.field[16:32] = "{0:016b}".format(2 ** 16 + self.value)
        else:
            # If immediate field is a directive we should go find the value inside table
            if self.value not in self.table:
                error = "Undefined label : %s" % self.value
                if self.line_index is not None:
                    error += " on line : %d" % self.line_index
                error += "."
                raise ValueError(error)
            if self.table[self.value] >= 0:
                self.field[16:32] = "{0:016b}".format(self.table[self.value])
            # Two's complement if negative:
            else:
                self.field[16:32] = "{0:016b}".format(2 ** 16 + self.table[self.value])

        return ''.join(self.field)


class IType3(Instruction):

    # todo 1-define regex
    regex = "([0-9]+),([0-9]+)"

    # todo 2-define field dictionaries
    op_code = {"jalr": "1100"}

    def __init__(self, instruction: Instruction):
        """
        Constructor for IType3 Instruction class
        """
        super().__init__(instruction.command, instruction.rest, instruction.line_index)

        # Extracting 2 operand register numbers:
        extract = re.findall(self.regex, self.rest)
        if len(extract) == 0:
            error = "Wrong register numbers"
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)
        extract = extract[0]
        destination, source = map(int, (extract[0], extract[1]))

        # Handling operand register number errors:
        error = ""
        if destination == 0:
            error += "Destination register can not be zero"
        elif destination > 15:
            if error != "":
                error += ", "
            error += "Destination register must be less than 16"
        elif source > 15:
            if error != "":
                error += ", "
            error += "Source register must be less than 16"
        if error != "":
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)

        # Setting operand register numbers up:
        self.destination, self.source = destination, source

    # todo 3-fill machine code
    @property
    def machine_code(self):
        self.field[4:8] = self.op_code[self.command]
        self.field[8:12] = "{0:04b}".format(self.source)
        self.field[12:16] = "{0:04b}".format(self.destination)
        return ''.join(self.field)


class JType(Instruction):

    # todo 1-define regex
    regex = "([-\w]+)"

    # todo 2-define field dictionaries
    op_code = {"j": "1101"}

    def __init__(self, instruction: Instruction, table):
        """
        Constructor for JType Instruction class
        :param: table: a dictionary that has labels with their values stored
        """
        super().__init__(instruction.command, instruction.rest, instruction.line_index)

        # Extracting and setting jump offset value up:
        extract = re.findall(self.regex, self.rest)
        self.table = table
        if len(extract) == 0:
            error = "Wrong label value"
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)
        self.value = extract[0]

    # todo 3-fill machine code
    @property
    def machine_code(self):
        self.field[4:8] = self.op_code[self.command]

        # Handling offset field set-up with errors:
        if self.value.lstrip("-").isdecimal():
            self.value = int(self.value)
            if self.value >= 2 ** 16:
                error = "Immediate(offset) value is too large : %d" % self.value
                if self.line_index is not None:
                    error += " on line : %d " % self.line_index
                error += "."
                raise ValueError(error)
            elif self.value < 0:
                error = "Immediate(offset) value couldn't be negative inside a jump"
                if self.line_index is not None:
                    error += " on line : %d " % self.line_index
                error += "."
                raise ValueError(error)
            else:
                self.field[16:32] = "{0:016b}".format(self.value)
        else:
            # If offset field is a label we should go find the address inside table
            if self.value not in self.table:
                error = "Undefined label : %s" % self.value
                if self.line_index is not None:
                    error += " on line : %d" % self.line_index
                error += "."
                raise ValueError(error)
            self.field[16:32] = "{0:016b}".format(self.table[self.value])
        return ''.join(self.field)


class HType(Instruction):

    # todo 1-define field dictionaries
    op_code = {"halt": "1110"}

    def __init__(self, instruction: Instruction):
        """
        Constructor for HType Instruction class
        """
        super().__init__(instruction.command, instruction.rest, instruction.line_index)

        # Check if redundant string came into single-command halt instruction:
        if len(self.rest) != 0:
            error = "Redundant halt instruction"
            if self.line_index is not None:
                error += " on line : %d" % self.line_index
            error += "."
            raise ValueError(error)

    # todo 2-fill machine code
    @property
    def machine_code(self):
        self.field[4:8] = self.op_code[self.command]
        return ''.join(self.field)


class Assembler:

    # todo 1-define regex
    regex = "(([A-Za-z][\w]*)[ \t]+)?[ \t]*(.+)[ \t]+(.*)"

    # todo 2-define directives table and memory
    table = {}
    memory = 0

    def __init__(self, asm):
        """
        Constructor for Assembler class
        Our task here is to process all lines of assembly code and initialize
            them to Instruction classes
        """
        self.lines = asm
        del_indices = []
        for index, line in enumerate(self.lines):
            # Deleting line comments:
            line = line.split("#")[0].strip()
            self.lines[index] = line

            # Check if line is dummy:
            if line.strip() == "":
                del_indices.append(index)
        # save machine codes inside list:
        self.mc = []
        # Deleting dummy lines:
        for index, line in enumerate(self.lines):
            if index not in del_indices:
                self.mc.append(line)

        self.mc_ = []
        for index, line in enumerate(self.mc):
            # Separate label, command and rest of an instruction:
            extract = re.findall(self.regex, line)
            if len(extract) == 0:
                # Halt's an exception!
                if line == "halt":
                    instruction = Instruction(line, "", index)
                    self.mc_.append(instruction)
                    continue
                else:
                    raise ValueError("No such instructions found on line %d." % index)
            extract = extract[0]
            label, command, rest = extract[1].strip(), extract[2].strip(), extract[3].strip()

            # Fill directive:
            if command == ".fill":
                if not rest.lstrip("-").isdecimal():
                    if rest not in self.table:
                        raise ValueError("No such label in table after .fill directive on line %d." % index)
                    rest = self.table[rest]
                else:
                    rest = int(rest)
                # Check if there is space in memory:
                if index <= 8192:
                        if label in self.table:
                            raise ValueError("Label already exists after .fill directive on line %d." % index)
                        self.table[label] = index
                else:
                    raise ValueError("Stack overflow! on line %d." % index)
                if rest >= 0:
                    self.mc_.append("{0:032b}".format(rest))
                # Make two's complement binary if result is negative:
                else:
                    self.mc_.append("{0:032b}".format(2 ** 32 + rest))

            # Space Directive
            elif command == ".space":
                # Fetching requested space(volume):
                if rest.lstrip("-").isdecimal():
                    volume = int(rest)
                elif rest in self.table:
                    volume = self.table[rest]
                else:
                    raise ValueError("No such label in table after .space directive on line %d." % index)
                if volume <= 0:
                    raise ValueError("No non-positive space reservation accepted on line %d." % index)
                # Check if there is enough space in memory:
                elif index + volume <= 8192:
                    if label in self.table:
                        raise ValueError("Label already exists after .space directive on line %d." % index)
                    self.table[label] = index
                else:
                    raise ValueError("Stack overflow! on line %d." % index)
                for i in range(0, volume):
                    self.mc_.append("{0:032b}".format(0))

            # Labeled halt's also an exception!
            elif rest == "halt":
                if len(command) > 6:
                    raise ValueError("Instruction label's size shouldn't be more than 6 : "
                                     "%s on line %d." % (command, index))
                if command in self.table:
                    raise ValueError("Label already defined : %s on line %d."
                                     % (command, index))
                self.table[command] = index
                instruction = Instruction(rest, "", index)
                self.mc_.append(instruction)

            # If there is label and we do not have directive:
            elif label != "":
                if len(label) > 6:
                    raise ValueError("Instruction label's size shouldn't be more than 6 : "
                                     "%s on line %d." % (label, index))
                if label in self.table:
                    raise ValueError("Label already defined : %s on line %d."
                                     % (label, index))
                self.table[label] = index
                instruction = Instruction(command, rest, index)
                self.mc_.append(instruction)

            # Normal non-labeled instruction:
            else:
                instruction = Instruction(command, rest, index)
                self.mc_.append(instruction)

    # todo 3-fill go function
    def go(self):
        assemble = ""
        for line in self.mc_:
            if type(line) is str:
                assemble += line
            elif line.type == "R":
                assemble += RType(line).machine_code
            elif line.type == "I1":
                assemble += IType1(line, self.table).machine_code
            elif line.type == "I2":
                assemble += IType2(line, self.table).machine_code
            elif line.type == "I3":
                assemble += IType3(line).machine_code
            elif line.type == "J":
                assemble += JType(line, self.table).machine_code
            elif line.type == "H":
                assemble += HType(line).machine_code
            assemble += "\n"
        return assemble


if __name__ == "__main__":
    while True:
        print(re.findall(Assembler.regex, input()))
