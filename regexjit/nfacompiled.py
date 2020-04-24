import jitbuilder
from regexjit.methods import AddMethod, StepMethod, ExecMethod, FindAllMethod
from regexjit.instruction import OpCode
from dataclasses import dataclass
from _regexutil import ffi, lib
import ctypes
import regexjit.ds as ds
import numpy as np


class NFA:
    def __init__(self, prog):
        self.prog = prog
        self.stack = []
        self.start = prog.start

        td = ds.RegexTypeDictionary()

        ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p

        # pc, t, pos, text, tl, slots, sl
        a = AddMethod(td, self.prog.instructions)
        ADDFUNC = ctypes.CFUNCTYPE(
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ds.Thread),
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
            ctypes.c_int,
        )
        c_a = jitbuilder.compile_method_builder(a)
        c_a_capsule = ctypes.pythonapi.PyCapsule_GetPointer(ctypes.py_object(c_a), None)
        self.compiled_add = ADDFUNC(c_a_capsule)

        # pc, t, pos, text, tl, slots, sl
        s = StepMethod(td, self.prog.instructions, c_a_capsule)

        STEPFUNC = ctypes.CFUNCTYPE(
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ds.Thread),
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
            ctypes.POINTER(ds.Thread),
        )
        c_s = jitbuilder.compile_method_builder(s)
        c_s_capsule = ctypes.pythonapi.PyCapsule_GetPointer(ctypes.py_object(c_s), None)
        self.compiled_step = STEPFUNC(c_s_capsule)

        e = ExecMethod(td, self.prog, c_s_capsule, c_a_capsule)

        # text, tl, slots, sl, nsubmatch, start
        EXECFUNC = ctypes.CFUNCTYPE(
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
        )
        c_e = jitbuilder.compile_method_builder(e)
        c_e_capsule = ctypes.pythonapi.PyCapsule_GetPointer(ctypes.py_object(c_e), None)
        self.compiled_exec = EXECFUNC(c_e_capsule)

        f = FindAllMethod(td, c_e_capsule)
        FINDALLFUNC = ctypes.CFUNCTYPE(
            ctypes.POINTER(ds.Matches),
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
            ctypes.c_int,
        )
        c_f = jitbuilder.compile_method_builder(f)
        c_f_capsule = ctypes.pythonapi.PyCapsule_GetPointer(ctypes.py_object(c_f), None)
        self.compiled_find_all = FINDALLFUNC(c_f_capsule)

    def find_first(self, text, tl, nsubmatch):
        slots = (ctypes.c_int * 2)(-1,-1)
        if self.compiled_exec(text, tl, ctypes.cast(slots, ctypes.POINTER(ctypes.c_int)), 2, nsubmatch, 0):
            return slots[0], slots[1]

        return None

    def find_all(self, text, tl, nsubmatch):
        slots = (ctypes.c_int * 2)(-1,-1)
        match_obj = self.compiled_find_all(text, tl, ctypes.cast(slots, ctypes.POINTER(ctypes.c_int)), 2, nsubmatch)
        # res = []
        # for i in range(match_obj.contents.nmatch):
        #     res.append((match_obj.contents.matches_slots[i][0], match_obj.contents.matches_slots[i][1]))
        return match_obj.contents.nmatch