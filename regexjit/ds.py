import ctypes
from jitbuilder import TypeDictionary


class SparseSet(ctypes.Structure):
    _fields_ = [
        ("dense", ctypes.POINTER(ctypes.c_int)),
        ("sparse", ctypes.POINTER(ctypes.c_int)),
        ("size", ctypes.c_int),
        ("capacity", ctypes.c_int),
        ("max_value", ctypes.c_int),
    ]


class Thread(ctypes.Structure):
    _fields_ = [
        ("caps", ctypes.POINTER(ctypes.c_int)),
        ("nslots", ctypes.c_int),
        ("set", ctypes.POINTER(SparseSet)),
    ]


class Matches(ctypes.Structure):
    _fields_ = [
        ("nmatch", ctypes.c_int),
        ("matches_slots_capacity", ctypes.c_int),
        ("matches_slots", ctypes.POINTER(ctypes.POINTER(ctypes.c_int))),
    ]


class RegexTypeDictionary(TypeDictionary):
    def __init__(self):
        super().__init__()
        self.define_struct("SparseSet")
        self.define_field("SparseSet", "dense", self.p_int_32, SparseSet.dense.offset)
        self.define_field("SparseSet", "sparse", self.p_int_32, SparseSet.sparse.offset)
        self.define_field("SparseSet", "size", self.int_32, SparseSet.size.offset)
        self.define_field(
            "SparseSet", "capacity", self.int_32, SparseSet.capacity.offset
        )
        self.define_field(
            "SparseSet", "max_value", self.int_32, SparseSet.max_value.offset
        )
        self.close_struct("SparseSet", ctypes.sizeof(SparseSet))

        self.define_struct("Thread")
        self.define_field("Thread", "caps", self.p_int_32, Thread.caps.offset)
        self.define_field("Thread", "nslots", self.int_32, Thread.nslots.offset)
        self.define_field(
            "Thread",
            "set",
            self.pointer_to(self.lookup_struct("SparseSet")),
            Thread.set.offset,
        )
        self.close_struct("Thread", ctypes.sizeof(Thread))

        self.define_struct("Matches")
        self.define_field("Matches", "nmatch", self.int_32, Matches.nmatch.offset)
        self.define_field(
            "Matches",
            "matches_slots_capacity",
            self.int_32,
            Matches.matches_slots_capacity.offset,
        )
        self.define_field(
            "Matches",
            "matches_slots",
            self.pointer_to(self.p_int_32),
            Matches.matches_slots.offset,
        )
        self.close_struct("Matches", ctypes.sizeof(Matches))

