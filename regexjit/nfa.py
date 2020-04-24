from regexjit.instruction import OpCode
from dataclasses import dataclass


class SparseSet:
    def __init__(self, size):
        self.dense = []
        self.sparse = [None] * size

    def capacity(self):
        return len(self.sparse)

    def length(self):
        return len(self.dense)

    def is_empty(self):
        return len(self.dense) == 0

    def insert(self, value):
        i = self.length()
        # assert i < self.capacity()
        self.dense.append(value)
        self.sparse[value] = i

    def contains(self, value):
        i = self.sparse[value]
        return i and i < self.length() and self.dense[i] == value

    def clear(self):
        self.dense.clear()


class Threads:
    def __init__(self):
        self.set = SparseSet(0)
        self.caps = []
        self.slots_per_thread = 2

    def resize(self, num_insts, ncaps):
        if num_insts == self.set.capacity():
            return
        self.slots_per_thread = ncaps
        self.set = SparseSet(num_insts)
        self.caps = [None] * (self.slots_per_thread * num_insts)

    def caps_(self, pc):
        i = pc * self.slots_per_thread
        return self.caps[i : i + self.slots_per_thread]


class NFA:
    def __init__(self, prog):
        self.prog = prog
        self.stack = []
        self.start = prog.start

    def exec(self, text, nsubmatch, start):
        text_length = len(text)

        matches = [False]

        ncapture = 2 * nsubmatch if not nsubmatch == 0 else 2
        self.slots = [-1] * ncapture

        self.clist = Threads()
        self.clist.resize(len(self.prog.instructions), ncapture)
        self.nlist = Threads()
        self.nlist.resize(len(self.prog.instructions), ncapture)

        self.clist.set.clear()
        self.nlist.set.clear()

        matched = False
        pos = start

        while True:
            if self.clist.set.is_empty():
                if (matched) or (pos != 0 and self.prog.anchor_start):
                    break

            if self.clist.set.is_empty() or (
                not self.prog.anchor_start and not matched
            ):
                self.add(
                    self.clist,
                    self.slots,
                    0,
                    text[pos] & 0xFF if pos < text_length else -1,
                    text,
                    pos,
                )

            for i in range(self.clist.set.length()):
                inst_id = self.clist.set.dense[i]
                if self.step(
                    self.nlist,
                    matches,
                    self.slots,
                    self.clist.caps_(inst_id),
                    inst_id,
                    text[pos] & 0xFF if pos < text_length else -1,
                    text[pos + 1] & 0xFF if pos + 1 < text_length else -1,
                    text,
                    pos,
                ):
                    matched = True
                    break
            if pos >= text_length:
                break

            pos += 1
            self.clist, self.nlist = self.nlist, self.clist
            self.nlist.set.clear()
        return matched

    def step(
        self, nlist, matches, slots, thread_caps, inst_id, byte, next_byte, text, pos
    ):
        ip = self.prog.instructions[inst_id]
        if ip.opcode == OpCode.ByteRange:
            if ip.matches(byte):
                self.add(nlist, thread_caps, ip.goto, next_byte, text, pos + 1)
                return False
        elif ip.opcode == OpCode.Match:
            if ip.match_id < len(matches):
                matches[ip.match_id] = True
                for i in range(len(self.slots)):
                    self.slots[i] = thread_caps[i]
            return True
        else:
            return False

    def add(self, nlist, thread_caps, inst_id, byte, text, pos):
        self.stack.append((inst_id, None))
        while self.stack:
            pc, capture_pos = self.stack.pop()
            if capture_pos != None:
                thread_caps[pc] = capture_pos
            else:
                self.add_step(nlist, thread_caps, pc, byte, text, pos, inst_id)

    def add_step(self, nlist, thread_caps, inst_id, byte, text, pos, inst_id2):
        while True:
            if nlist.set.contains(inst_id):
                return
            nlist.set.insert(inst_id)
            ip = self.prog.instructions[inst_id]

            if ip.opcode == OpCode.Split:
                self.stack.append((ip.alternate_goto, None))
                inst_id = ip.goto
            elif ip.opcode == OpCode.Save:
                if ip.slot < len(thread_caps):
                    self.stack.append((ip.slot, thread_caps[ip.slot]))
                    thread_caps[ip.slot] = pos
                inst_id = ip.goto
            elif ip.opcode == OpCode.ByteRange or ip.opcode == OpCode.Match:
                t = nlist.caps_(inst_id)
                for i in range(len(t)):
                    t[i] = thread_caps[i]

                i = inst_id * self.clist.slots_per_thread
                nlist.caps[i : i + nlist.slots_per_thread] = t
                return
            elif ip.opcode == OpCode.EmptyLook:
                if ip.is_empty_match(text, pos):
                    inst_id = ip.goto

