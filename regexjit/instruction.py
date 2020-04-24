from dataclasses import dataclass
from enum import Enum

OpCode = Enum("OpCode", "Split ByteRange Save EmptyLook Match")

EmptyOp = Enum(
    "EmptyOp",
    "BeginLine BeginText EndLine EndText WordBoundary NonWordBoundary WordBoundaryAscii NonWordBoundaryAscii",
)


@dataclass
class ByteRange:
    start: int
    end: int


class Instruction:
    def __init__(
        self,
        goto=None,
        alternate_goto=None,
        slot=None,
        match_id=None,
        byte_range=None,
        empty_look=None,
        opcode=None,
    ):
        self.goto = goto
        self.alternate_goto = alternate_goto
        self.slot = slot
        self.match_id = match_id
        self.byte_range = byte_range
        self.empty_look = empty_look
        self.opcode = opcode

    @classmethod
    def init_split(cls, inst):
        return cls(
            goto=inst.goto, alternate_goto=inst.alternate_goto, opcode=OpCode.Split
        )

    @classmethod
    def init_byte_range(cls, inst):
        br = ByteRange(inst.start, inst.end)
        return cls(goto=inst.goto, byte_range=br, opcode=OpCode.ByteRange)

    @classmethod
    def init_save(cls, inst):
        return cls(goto=inst.goto, slot=inst.slot, opcode=OpCode.Save)

    @classmethod
    def init_match(cls, inst):
        return cls(match_id=inst.match_id, opcode=OpCode.Match)

    @classmethod
    def init_empty_look(cls, inst):
        empty = inst.kind
        if empty == "StartLine":
            empty = EmptyOp.BeginLine
        elif empty == "StartText":
            empty = EmptyOp.BeginText
        elif empty == "EndLine":
            empty = EmptyOp.EndLine
        elif empty == "EndText":
            empty = EmptyOp.EndText
        elif empty == "NotWordBoundary":
            empty = EmptyOp.NonWordBoundary
        elif empty == "WordBoundary":
            empty = EmptyOp.WordBoundary
        elif empty == "WordBoundaryAscii":
            empty = EmptyOp.WordBoundaryAscii
        elif empty == "NotWordBoundaryAscii":
            empty = EmptyOp.NonWordBoundaryAscii
        return cls(goto=inst.goto, empty_look=empty, opcode=OpCode.EmptyLook)

    def matches(self, byte):
        return self.byte_range.start <= byte <= self.byte_range.end

    def is_empty_match(self, text, pos):
        if self.empty_look == EmptyOp.BeginLine:
            return pos == 0 or text[pos - 1] == "\n"
        elif self.empty_look == EmptyOp.BeginText:
            return pos == 0
        elif self.empty_look == EmptyOp.EndLine:
            return pos == len(text) or text[pos] == "\n"
        elif self.empty_look == EmptyOp.EndText:
            return pos == len(text)
        elif self.empty_look == EmptyOp.WordBoundary:
            return self.is_word_byte(
                text[pos - 1] & 0xFF if pos - 1 > -1 and pos - 1 < len(text) else -1
            ) != self.is_word_byte(text[pos] & 0xFF if pos < len(text) else -1)
        elif self.empty_look == EmptyOp.WordBoundaryAscii:
            return self.is_word_byte(
                text[pos - 1] & 0xFF if pos - 1 < len(text) else -1
            ) != self.is_word_byte(text[pos] & 0xFF if pos < len(text) else -1)
        elif self.empty_look == EmptyOp.NonWordBoundary:
            return self.is_word_byte(
                text[pos - 1] & 0xFF if pos - 1 > -1 and pos - 1 < len(text) else -1
            ) == self.is_word_byte(text[pos] & 0xFF if pos < len(text) else -1)
        elif self.empty_look == EmptyOp.NonWordBoundaryAscii:
            return self.is_word_byte(
                text[pos - 1] & 0xFF if pos - 1 < len(text) else -1
            ) == self.is_word_byte(text[pos] & 0xFF if pos < len(text) else -1)

    @staticmethod
    def is_word_byte(byte):
        if byte == -1:
            return False
        return (
            ord("A") <= byte <= ord("Z")
            or ord("a") <= byte <= ord("z")
            or ord("0") <= byte <= ord("9")
            or chr(byte) == "_"
        )
