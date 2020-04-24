import regexcompiler
from regexjit.instruction import Instruction, EmptyOp
from regexjit.nfa import NFA

from enum import Enum

MatchKind = Enum("MatchKind", "FirstMatch LongestMatch FullMatch")
Anchor = Enum("Anchor", "UnAnchored Anchored")


def compile_regex(regex):
    prog = regexcompiler.compile_regex(regex)
    instructions = []

    for instruction in prog.instructions:
        if instruction.kind == "split":
            instructions.append(Instruction.init_split(instruction))
        elif instruction.kind == "bytes":
            instructions.append(Instruction.init_byte_range(instruction))
        elif instruction.kind == "save":
            instructions.append(Instruction.init_save(instruction))
        elif instruction.kind == "match":
            instructions.append(Instruction.init_match(instruction))
        else:
            instructions.append(Instruction.init_empty_look(instruction))

    return Program(
        instructions,
        prog.start,
        prog.is_anchored_start,
        prog.is_anchored_end,
        prog.has_unicode_word_boundary,
        regex,
    )


class Program:
    def __init__(
        self,
        instructions,
        start,
        anchor_start,
        anchor_end,
        has_unicode_word_boundary,
        regex,
    ):
        self.instructions = instructions
        self.start = start
        self.size = len(instructions)
        self.anchor_start = anchor_start
        self.anchor_end = anchor_end
        self.has_unicode_word_boundary = has_unicode_word_boundary
        self.regex = regex
        self.nfa = NFA(self)

    def dump(self):
        return regexcompiler.dump_bytecode(self.regex)

    def find_first(self, text, nsubmatch):
        if self.nfa.exec(text, nsubmatch, 0):
            return self.nfa.slots
        return None

    def find_all(self, text, nsubmatch):
        text_length = len(text)
        last_end = 0
        last_match = -1
        match_locations = []

        while True:
            if last_end > text_length:
                break
            if self.nfa.exec(text, nsubmatch, last_end):
                if self.nfa.slots[0] == self.nfa.slots[1]:
                    last_end = self.nfa.slots[1]+1
                    if self.nfa.slots[1] == last_match:
                        continue
                else:
                    last_end = self.nfa.slots[1]
                last_match = self.nfa.slots[1]
                match_locations.append(self.nfa.slots)
            else:
                break
        return match_locations
