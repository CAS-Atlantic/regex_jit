import jitbuilder
from regexjit.instruction import OpCode, EmptyOp
from _regexutil import ffi, lib
import ctypes


class AddMethod(jitbuilder.MethodBuilder):
    def __init__(self, td: jitbuilder.TypeDictionary, instructions):
        super().__init__(td)
        self.td = td
        self.instructions = instructions
        self.define_name("add")

        # pc, t, pos, text, tl, thread_caps, ncaps, thread_caps_start_idx
        self.define_parameter("pc", self.td.int_32)
        self.define_parameter("t", self.td.pointer_to(self.td.lookup_struct("Thread")))
        self.define_parameter("pos", self.td.int_32)

        self.define_array_parameter("text", self.td.p_int_8)
        self.define_parameter("tl", self.td.int_32)
        self.define_array_parameter("thread_caps", self.td.p_int_32)
        self.define_parameter("ncaps", self.td.int_32)
        self.define_parameter("thread_caps_idx", self.td.int_32)

        self.define_local("byte", self.td.int_8)
        self.define_local("byte_1", self.td.int_8)

        self.define_return_type(self.td.no_type)

        self.define_function(
            "contains",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "sparseset_contains"))),
            self.td.int_32,
            2,
            [self.td.pointer_to(self.td.lookup_struct("SparseSet")), self.td.int_32],
        )

        self.define_function(
            "insert",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "sparseset_insert"))),
            self.td.int_32,
            2,
            [self.td.pointer_to(self.td.lookup_struct("SparseSet")), self.td.int_32],
        )

        self.define_function(
            "is_word_byte",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "is_word_byte"))),
            self.td.int_32,
            1,
            [self.td.int_32],
        )

    def buildIL(self):
        self.all_locals_have_been_defined()

        contains = self.if_then(
            None,
            self.not_equal_to(
                self.call(
                    "contains",
                    2,
                    [
                        self.load_indirect("Thread", "set", self.load("t")),
                        self.load("pc"),
                    ],
                ),
                self.const_int_32(-1),
            ),
        )
        contains.return_()

        self.call(
            "insert",
            2,
            [self.load_indirect("Thread", "set", self.load("t")), self.load("pc")],
        )

        """
        BUILD UP SWITCH STATEMENT
        """
        switch_cases = []
        for inst_id, ip in enumerate(self.instructions):
            if ip.opcode == OpCode.EmptyLook:
                case, case_bldr = self.make_case(inst_id, None, False)
                switch_cases.append(case)
                nextpc = ip.goto

                if ip.empty_look == EmptyOp.BeginLine:
                    negative_pos_builder = case_bldr.orphan_builder()
                    negative_pos = negative_pos_builder.less_than(
                        negative_pos_builder.add(
                            negative_pos_builder.load("pos"),
                            negative_pos_builder.const_int_32(-1),
                        ),
                        negative_pos_builder.const_int_32(0),
                    )

                    is_newline_builder = case_bldr.orphan_builder()
                    prev = is_newline_builder.load_at(
                        self.td.p_int_8,
                        is_newline_builder.index_at(
                            self.td.p_int_8,
                            is_newline_builder.load("text"),
                            is_newline_builder.add(
                                is_newline_builder.load("pos"),
                                is_newline_builder.const_int_32(-1),
                            ),
                        ),
                    )
                    is_newline = is_newline_builder.equal_to(
                        prev, is_newline_builder.const_int_8(ord("\n"))
                    )
                    return_conditions = [
                        case_bldr.make_condition(negative_pos_builder, negative_pos),
                        case_bldr.make_condition(is_newline_builder, is_newline),
                    ]

                    any_true, _ = case_bldr.if_or(None, None, 2, return_conditions)
                    any_true.call(
                        "add",
                        8,
                        [
                            any_true.const_int_32(nextpc),
                            any_true.load("t"),
                            any_true.load("pos"),
                            any_true.load("text"),
                            any_true.load("tl"),
                            any_true.load("thread_caps"),
                            any_true.load("ncaps"),
                            any_true.load("thread_caps_idx"),
                        ],
                    )

                elif ip.empty_look == EmptyOp.BeginText:
                    begin_text_builder = case_bldr.if_then(
                        None,
                        case_bldr.equal_to(
                            case_bldr.load("pos"), case_bldr.const_int_32(0)
                        ),
                    )
                    begin_text_builder.call(
                        "add",
                        8,
                        [
                            begin_text_builder.const_int_32(nextpc),
                            begin_text_builder.load("t"),
                            begin_text_builder.load("pos"),
                            begin_text_builder.load("text"),
                            begin_text_builder.load("tl"),
                            begin_text_builder.load("thread_caps"),
                            begin_text_builder.load("ncaps"),
                            begin_text_builder.load("thread_caps_idx"),
                        ],
                    )

                elif ip.empty_look == EmptyOp.EndLine:
                    eof_pos_builder = case_bldr.orphan_builder()
                    eof_pos = eof_pos_builder.equal_to(
                        eof_pos_builder.load("pos"), eof_pos_builder.load("tl")
                    )

                    is_newline_builder = case_bldr.orphan_builder()
                    curr = case_bldr.load_at(
                        self.td.p_int_8,
                        case_bldr.index_at(
                            self.td.p_int_8,
                            case_bldr.load("text"),
                            case_bldr.load("pos"),
                        ),
                    )

                    is_newline = is_newline_builder.equal_to(
                        curr, is_newline_builder.const_int_8(ord("\n"))
                    )
                    return_conditions = [
                        case_bldr.make_condition(eof_pos_builder, eof_pos),
                        case_bldr.make_condition(is_newline_builder, is_newline),
                    ]
                    any_true, _ = case_bldr.if_or(None, None, 2, return_conditions)
                    any_true.call(
                        "add",
                        8,
                        [
                            any_true.const_int_32(nextpc),
                            any_true.load("t"),
                            any_true.load("pos"),
                            any_true.load("text"),
                            any_true.load("tl"),
                            any_true.load("thread_caps"),
                            any_true.load("ncaps"),
                            any_true.load("thread_caps_idx"),
                        ],
                    )

                elif ip.empty_look == EmptyOp.EndText:
                    end_text_builder = case_bldr.if_then(
                        None,
                        case_bldr.equal_to(case_bldr.load("pos"), case_bldr.load("tl")),
                    )

                    end_text_builder.call(
                        "add",
                        8,
                        [
                            end_text_builder.const_int_32(nextpc),
                            end_text_builder.load("t"),
                            end_text_builder.load("pos"),
                            end_text_builder.load("text"),
                            end_text_builder.load("tl"),
                            end_text_builder.load("thread_caps"),
                            end_text_builder.load("ncaps"),
                            end_text_builder.load("thread_caps_idx"),
                        ],
                    )

                elif ip.empty_look == EmptyOp.WordBoundary:
                    pos_1_lt_l_builder = case_bldr.orphan_builder()
                    pos_1_lt_l = pos_1_lt_l_builder.less_than(
                        pos_1_lt_l_builder.sub(
                            pos_1_lt_l_builder.load("pos"),
                            pos_1_lt_l_builder.const_int_32(1),
                        ),
                        pos_1_lt_l_builder.load("tl"),
                    )

                    pos_1_gt_zero_builder = case_bldr.orphan_builder()
                    pos_1_gt_zero = pos_1_gt_zero_builder.greater_than(
                        pos_1_gt_zero_builder.sub(
                            pos_1_gt_zero_builder.load("pos"),
                            pos_1_gt_zero_builder.const_int_32(1),
                        ),
                        pos_1_gt_zero_builder.const_int_32(-1),
                    )

                    pos_1_conditions = [
                        case_bldr.make_condition(pos_1_gt_zero_builder, pos_1_gt_zero),
                        case_bldr.make_condition(pos_1_lt_l_builder, pos_1_lt_l),
                    ]

                    pos_1_ok, pos_1_n_ok = case_bldr.if_and(
                        None, None, 2, pos_1_conditions
                    )

                    pos_1_ok.store(
                        "byte_1",
                        pos_1_ok.load_at(
                            self.td.p_int_8,
                            pos_1_ok.index_at(
                                self.td.p_int_8,
                                pos_1_ok.load("text"),
                                pos_1_ok.sub(
                                    pos_1_ok.load("pos"), pos_1_ok.const_int_32(1)
                                ),
                            ),
                        ),
                    )

                    pos_1_n_ok.store("byte_1", pos_1_n_ok.const_int_8(-1))

                    pos_ok, pos_n_ok = case_bldr.if_then_else(
                        None,
                        None,
                        case_bldr.less_than(
                            case_bldr.load("pos"), case_bldr.load("tl")
                        ),
                    )

                    pos_ok.store(
                        "byte",
                        pos_ok.load_at(
                            self.td.p_int_8,
                            pos_ok.index_at(
                                self.td.p_int_8, pos_ok.load("text"), pos_ok.load("pos")
                            ),
                        ),
                    )
                    pos_n_ok.store("byte", pos_n_ok.const_int_8(-1))

                    do_add = case_bldr.if_then(
                        None,
                        case_bldr.not_equal_to(
                            case_bldr.call(
                                "is_word_byte", 1, [case_bldr.load("byte_1")]
                            ),
                            case_bldr.call("is_word_byte", 1, [case_bldr.load("byte")]),
                        ),
                    )

                    do_add.call(
                        "add",
                        8,
                        [
                            do_add.const_int_32(nextpc),
                            do_add.load("t"),
                            do_add.load("pos"),
                            do_add.load("text"),
                            do_add.load("tl"),
                            do_add.load("thread_caps"),
                            do_add.load("ncaps"),
                            do_add.load("thread_caps_idx"),
                        ],
                    )

                elif ip.empty_look == EmptyOp.NonWordBoundary:
                    pos_1_lt_l_builder = case_bldr.orphan_builder()
                    pos_1_lt_l = pos_1_lt_l_builder.less_than(
                        pos_1_lt_l_builder.sub(
                            pos_1_lt_l_builder.load("pos"),
                            pos_1_lt_l_builder.const_int_32(1),
                        ),
                        pos_1_lt_l_builder.load("tl"),
                    )

                    pos_1_gt_zero_builder = case_bldr.orphan_builder()
                    pos_1_gt_zero = pos_1_gt_zero_builder.greater_than(
                        pos_1_gt_zero_builder.sub(
                            pos_1_gt_zero_builder.load("pos"),
                            pos_1_gt_zero_builder.const_int_32(1),
                        ),
                        pos_1_gt_zero_builder.const_int_32(-1),
                    )

                    pos_1_conditions = [
                        case_bldr.make_condition(pos_1_gt_zero_builder, pos_1_gt_zero),
                        case_bldr.make_condition(pos_1_lt_l_builder, pos_1_lt_l),
                    ]

                    pos_1_ok, pos_1_n_ok = case_bldr.if_and(
                        None, None, 2, pos_1_conditions
                    )

                    pos_1_ok.store(
                        "byte_1",
                        pos_1_ok.load_at(
                            self.td.p_int_8,
                            pos_1_ok.index_at(
                                self.td.p_int_8,
                                pos_1_ok.load("text"),
                                pos_1_ok.sub(
                                    pos_1_ok.load("pos"), pos_1_ok.const_int_32(1)
                                ),
                            ),
                        ),
                    )

                    pos_1_n_ok.store("byte_1", pos_1_n_ok.const_int_8(-1))

                    pos_ok, pos_n_ok = case_bldr.if_then_else(
                        None,
                        None,
                        case_bldr.less_than(
                            case_bldr.load("pos"), case_bldr.load("tl")
                        ),
                    )

                    pos_ok.store(
                        "byte",
                        pos_ok.load_at(
                            self.td.p_int_8,
                            pos_ok.index_at(
                                self.td.p_int_8, pos_ok.load("text"), pos_ok.load("pos")
                            ),
                        ),
                    )
                    pos_n_ok.store("byte", pos_n_ok.const_int_8(-1))

                    do_add = case_bldr.if_then(
                        None,
                        case_bldr.equal_to(
                            case_bldr.call(
                                "is_word_byte", 1, [case_bldr.load("byte_1")]
                            ),
                            case_bldr.call("is_word_byte", 1, [case_bldr.load("byte")]),
                        ),
                    )

                    do_add.call(
                        "add",
                        8,
                        [
                            do_add.const_int_32(nextpc),
                            do_add.load("t"),
                            do_add.load("pos"),
                            do_add.load("text"),
                            do_add.load("tl"),
                            do_add.load("thread_caps"),
                            do_add.load("ncaps"),
                            do_add.load("thread_caps_idx"),
                        ],
                    )

            elif ip.opcode == OpCode.Save:
                case, case_bldr = self.make_case(inst_id, None, False)
                switch_cases.append(case)
                nextpc = ip.goto
                slot_gte_nsubmatches, n_slot_gte_nsubmatches = case_bldr.if_then_else(
                    None,
                    None,
                    case_bldr.greater_or_equal_to(
                        case_bldr.const_int_32(ip.slot), case_bldr.load("ncaps")
                    ),
                )
                slot_gte_nsubmatches.call(
                    "add",
                    8,
                    [
                        slot_gte_nsubmatches.const_int_32(nextpc),
                        slot_gte_nsubmatches.load("t"),
                        slot_gte_nsubmatches.load("pos"),
                        slot_gte_nsubmatches.load("text"),
                        slot_gte_nsubmatches.load("tl"),
                        slot_gte_nsubmatches.load("thread_caps"),
                        slot_gte_nsubmatches.load("ncaps"),
                        slot_gte_nsubmatches.load("thread_caps_idx"),
                    ],
                )

                n_slot_gte_nsubmatches.store(
                    "old",
                    n_slot_gte_nsubmatches.load_at(
                        self.td.p_int_32,
                        n_slot_gte_nsubmatches.index_at(
                            self.td.p_int_32,
                            n_slot_gte_nsubmatches.load("thread_caps"),
                            n_slot_gte_nsubmatches.add(
                                n_slot_gte_nsubmatches.const_int_32(ip.slot),
                                n_slot_gte_nsubmatches.load("thread_caps_idx"),
                            ),
                        ),
                    ),
                )

                n_slot_gte_nsubmatches.store_at(
                    n_slot_gte_nsubmatches.index_at(
                        self.td.p_int_32,
                        n_slot_gte_nsubmatches.load("thread_caps"),
                        n_slot_gte_nsubmatches.add(
                            n_slot_gte_nsubmatches.const_int_32(ip.slot),
                            n_slot_gte_nsubmatches.load("thread_caps_idx"),
                        ),
                    ),
                    n_slot_gte_nsubmatches.load("pos"),
                )

                n_slot_gte_nsubmatches.call(
                    "add",
                    8,
                    [
                        n_slot_gte_nsubmatches.const_int_32(nextpc),
                        n_slot_gte_nsubmatches.load("t"),
                        n_slot_gte_nsubmatches.load("pos"),
                        n_slot_gte_nsubmatches.load("text"),
                        n_slot_gte_nsubmatches.load("tl"),
                        n_slot_gte_nsubmatches.load("thread_caps"),
                        n_slot_gte_nsubmatches.load("ncaps"),
                        n_slot_gte_nsubmatches.load("thread_caps_idx"),
                    ],
                )

                n_slot_gte_nsubmatches.store_at(
                    n_slot_gte_nsubmatches.index_at(
                        self.td.p_int_32,
                        n_slot_gte_nsubmatches.load("thread_caps"),
                        n_slot_gte_nsubmatches.add(
                            n_slot_gte_nsubmatches.const_int_32(ip.slot),
                            n_slot_gte_nsubmatches.load("thread_caps_idx"),
                        ),
                    ),
                    n_slot_gte_nsubmatches.load("pos"),
                )

            elif ip.opcode == OpCode.Split:
                case, case_bldr = self.make_case(inst_id, None, False)
                switch_cases.append(case)
                case_bldr.call(
                    "add",
                    8,
                    [
                        case_bldr.const_int_32(ip.goto),
                        case_bldr.load("t"),
                        case_bldr.load("pos"),
                        case_bldr.load("text"),
                        case_bldr.load("tl"),
                        case_bldr.load("thread_caps"),
                        case_bldr.load("ncaps"),
                        case_bldr.load("thread_caps_idx"),
                    ],
                )
                case_bldr.call(
                    "add",
                    8,
                    [
                        case_bldr.const_int_32(ip.alternate_goto),
                        case_bldr.load("t"),
                        case_bldr.load("pos"),
                        case_bldr.load("text"),
                        case_bldr.load("tl"),
                        case_bldr.load("thread_caps"),
                        case_bldr.load("ncaps"),
                        case_bldr.load("thread_caps_idx"),
                    ],
                )

        default_bldr = self.switch("pc", None, len(switch_cases), switch_cases)
        default_bldr.store("other_start_idx", default_bldr.load("thread_caps_idx"))
        default_bldr.store(
            "start_idx",
            default_bldr.mul(
                default_bldr.load_indirect("Thread", "nslots", default_bldr.load("t")),
                default_bldr.load("pc"),
            ),
        )

        copy_capture_loop = default_bldr.for_loop_up(
            "i",
            None,
            default_bldr.load("start_idx"),
            default_bldr.add(
                default_bldr.load("start_idx"),
                default_bldr.load_indirect("Thread", "nslots", default_bldr.load("t")),
            ),
            default_bldr.const_int_32(1),
        )

        copy_capture_loop.store_at(
            copy_capture_loop.index_at(
                self.td.p_int_32,
                copy_capture_loop.load_indirect(
                    "Thread", "caps", copy_capture_loop.load("t")
                ),
                copy_capture_loop.load("i"),
            ),
            copy_capture_loop.load_at(
                self.td.p_int_32,
                copy_capture_loop.index_at(
                    self.td.p_int_32,
                    copy_capture_loop.load("thread_caps"),
                    copy_capture_loop.load("other_start_idx"),
                ),
            ),
        )

        copy_capture_loop.store(
            "other_start_idx",
            copy_capture_loop.add(
                copy_capture_loop.load("other_start_idx"),
                copy_capture_loop.const_int_32(1),
            ),
        )

        self.return_()
        return True


class StepMethod(jitbuilder.MethodBuilder):
    def __init__(self, td: jitbuilder.TypeDictionary, instructions, add_fn):
        super().__init__(td)
        self.td = td
        self.instructions = instructions

        self.define_name("step")

        # pc, t, pos, text, tl, slots, sl, thread_caps
        self.define_parameter("pc", self.td.int_32)
        self.define_parameter("t", self.td.pointer_to(self.td.lookup_struct("Thread")))
        self.define_parameter("pos", self.td.int_32)
        self.define_array_parameter("text", self.td.p_int_8)
        self.define_parameter("tl", self.td.int_32)
        self.define_array_parameter("slots", self.td.p_int_32)
        self.define_parameter("sl", self.td.int_32)
        self.define_array_parameter("thread_caps", self.td.p_int_32)

        self.define_function(
            "add",
            __file__,
            "NA",
            add_fn,
            self.td.no_type,
            8,
            [
                self.td.int_32,
                self.td.pointer_to(self.td.lookup_struct("Thread")),
                self.td.int_32,
                self.td.p_int_8,
                self.td.int_32,
                self.td.p_int_32,
                self.td.int_32,
                self.td.int_32,
            ],
        )

        self.define_function(
            "matches",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "matches"))),
            self.td.int_32,
            3,
            [self.td.int_32, self.td.int_32, self.td.int_32],
        )

        self.define_return_type(self.td.int_32)

    def buildIL(self):
        self.all_locals_have_been_defined()

        switch_cases = []

        for inst_id, ip in enumerate(self.instructions):
            if ip.opcode == OpCode.Match:
                case, case_bldr = self.make_case(inst_id, None, False)
                switch_cases.append(case)

                case_bldr.store(
                    "start_idx",
                    case_bldr.mul(
                        case_bldr.load_indirect(
                            "Thread", "nslots", case_bldr.load("thread_caps")
                        ),
                        case_bldr.load("pc"),
                    ),
                )

                copy_capture_loop = case_bldr.for_loop_up(
                    "i",
                    None,
                    case_bldr.const_int_32(0),
                    case_bldr.load("sl"),
                    case_bldr.const_int_32(1),
                )

                copy_capture_loop.store_at(
                    copy_capture_loop.index_at(
                        self.td.p_int_32,
                        copy_capture_loop.load("slots"),
                        copy_capture_loop.load("i"),
                    ),
                    copy_capture_loop.load_at(
                        self.td.p_int_32,
                        copy_capture_loop.index_at(
                            self.td.p_int_32,
                            copy_capture_loop.load_indirect(
                                "Thread", "caps", copy_capture_loop.load("thread_caps")
                            ),
                            copy_capture_loop.add(
                                copy_capture_loop.load("i"),
                                copy_capture_loop.load("start_idx"),
                            ),
                        ),
                    ),
                )

                case_bldr.return_(case_bldr.const_int_32(1))
            elif ip.opcode == OpCode.ByteRange:
                case, case_bldr = self.make_case(inst_id, None, False)
                switch_cases.append(case)

                matches = case_bldr.if_then(
                    None,
                    case_bldr.equal_to(
                        case_bldr.call(
                            "matches",
                            3,
                            [
                                case_bldr.load_at(
                                    self.td.p_int_8,
                                    case_bldr.index_at(
                                        self.td.p_int_8,
                                        case_bldr.load("text"),
                                        case_bldr.load("pos"),
                                    ),
                                ),
                                case_bldr.const_int_32(ip.byte_range.start),
                                case_bldr.const_int_32(ip.byte_range.end),
                            ],
                        ),
                        case_bldr.const_int_32(1),
                    ),
                )
                matches.call(
                    "add",
                    8,
                    [
                        matches.const_int_32(ip.goto),
                        matches.load("t"),
                        matches.add(matches.load("pos"), matches.const_int_32(1)),
                        matches.load("text"),
                        matches.load("tl"),
                        matches.load_indirect(
                            "Thread", "caps", matches.load("thread_caps")
                        ),
                        matches.load_indirect(
                            "Thread", "nslots", matches.load("thread_caps")
                        ),
                        matches.mul(
                            matches.load_indirect(
                                "Thread", "nslots", matches.load("thread_caps")
                            ),
                            matches.load("pc"),
                        ),
                    ],
                )

                case_bldr.return_(case_bldr.const_int_32(0))

        default_bldr = self.switch("pc", None, len(switch_cases), switch_cases)
        default_bldr.return_(default_bldr.const_int_32(0))
        self.return_(self.const_int_32(0))
        return True


class ExecMethod(jitbuilder.MethodBuilder):
    def __init__(self, td: jitbuilder.TypeDictionary, prog, step_fn, add_fn):
        super().__init__(td)
        self.prog = prog
        self.td = td
        self.define_name("exec")

        # text, tl, slots, sl, nsubmatch, start
        self.define_array_parameter("text", self.td.p_int_8)
        self.define_parameter("tl", self.td.int_32)
        self.define_array_parameter("slots", self.td.p_int_32)
        self.define_parameter("sl", self.td.int_32)
        self.define_parameter("ncaps", self.td.int_32)
        self.define_parameter("start", self.td.int_32)

        self.define_local("matched", self.td.int_32)
        self.define_local("pos", self.td.int_32)
        self.define_local("one", self.td.int_32)
        self.define_local("clist", self.td.pointer_to(self.td.lookup_struct("Thread")))
        self.define_local("nlist", self.td.pointer_to(self.td.lookup_struct("Thread")))

        self.define_function(
            "contains",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "sparseset_contains"))),
            self.td.int_32,
            2,
            [self.td.pointer_to(self.td.lookup_struct("SparseSet")), self.td.int_32],
        )

        self.define_function(
            "insert",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "sparseset_insert"))),
            self.td.int_32,
            2,
            [self.td.pointer_to(self.td.lookup_struct("SparseSet")), self.td.int_32],
        )

        self.define_function(
            "remove",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "sparseset_remove"))),
            self.td.no_type,
            2,
            [self.td.pointer_to(self.td.lookup_struct("SparseSet")), self.td.int_32],
        )

        self.define_function(
            "clear",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "sparseset_clear"))),
            self.td.no_type,
            1,
            [self.td.pointer_to(self.td.lookup_struct("SparseSet"))],
        )

        self.define_function(
            "swap",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "thread_swap"))),
            self.td.no_type,
            2,
            [
                self.td.pointer_to(self.td.lookup_struct("Thread")),
                self.td.pointer_to(self.td.lookup_struct("Thread")),
            ],
        )

        self.define_function(
            "new_sparseset",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "sparseset_init"))),
            self.td.pointer_to(self.td.lookup_struct("SparseSet")),
            2,
            [self.td.int_32, self.td.int_32],
        )

        self.define_function(
            "destroy_sparseset",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "sparseset_deinit"))),
            self.td.no_type,
            1,
            [self.td.pointer_to(self.td.lookup_struct("SparseSet"))],
        )
        # Thread *thread_init(int numInsts, int nCaps)
        self.define_function(
            "new_thread",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "thread_init"))),
            self.td.pointer_to(self.td.lookup_struct("Thread")),
            2,
            [self.td.int_32, self.td.int_32],
        )

        self.define_function(
            "step",
            __file__,
            "NA",
            step_fn,
            self.td.int_32,
            8,
            [
                self.td.int_32,
                self.td.pointer_to(self.td.lookup_struct("Thread")),
                self.td.int_32,
                self.td.p_int_8,
                self.td.int_32,
                self.td.p_int_32,
                self.td.int_32,
                self.td.p_int_32,
            ],
        )

        self.define_function(
            "add",
            __file__,
            "NA",
            add_fn,
            self.td.no_type,
            8,
            [
                self.td.int_32,
                self.td.pointer_to(self.td.lookup_struct("Thread")),
                self.td.int_32,
                self.td.p_int_8,
                self.td.int_32,
                self.td.p_int_32,
                self.td.int_32,
                self.td.int_32,
            ],
        )

        self.define_return_type(self.td.int_32)

    def buildIL(self):
        self.all_locals_have_been_defined()

        self.store("matched", self.const_int_32(0))
        self.store("pos", self.load("start"))
        self.store("one", self.const_int_32(1))

        self.store(
            "clist",
            self.call(
                "new_thread",
                2,
                [self.const_int_32(len(self.prog.instructions)), self.load("ncaps")],
            ),
        )
        self.store(
            "nlist",
            self.call(
                "new_thread",
                2,
                [self.const_int_32(len(self.prog.instructions)), self.load("ncaps")],
            ),
        )

        self.call("clear", 1, [self.load_indirect("Thread", "set", self.load("nlist"))])

        self.call("clear", 1, [self.load_indirect("Thread", "set", self.load("clist"))])

        loop, break_bldr = self.while_do_loop_with_break("one", None, None)

        clist_is_empty_1 = loop.if_then(
            None,
            loop.equal_to(
                loop.load_indirect(
                    "SparseSet",
                    "size",
                    loop.load_indirect("Thread", "set", loop.load("clist")),
                ),
                loop.const_int_32(0),
            ),
        )

        matched_builder, matched_n_builder = clist_is_empty_1.if_then_else(
            None,
            None,
            clist_is_empty_1.equal_to(
                clist_is_empty_1.load("matched"), clist_is_empty_1.const_int_32(1)
            ),
        )

        matched_builder.goto(break_bldr)

        n_is_start_builder = matched_n_builder.orphan_builder()
        n_is_start = n_is_start_builder.not_equal_to(
            n_is_start_builder.load("pos"), n_is_start_builder.const_int_32(0)
        )
        is_anchored_start_builder = matched_n_builder.orphan_builder()
        is_anchored_start_1 = is_anchored_start_builder.equal_to(
            is_anchored_start_builder.const_int_32(self.prog.anchor_start),
            is_anchored_start_builder.const_int_32(1),
        )
        bail_out_cases_2 = [
            matched_n_builder.make_condition(
                is_anchored_start_builder, is_anchored_start_1
            ),
            matched_n_builder.make_condition(n_is_start_builder, n_is_start),
        ]

        all_true, _ = matched_n_builder.if_and(None, None, 2, bail_out_cases_2)
        all_true.goto(break_bldr)

        clist_is_empty, n_clist_is_empty = loop.if_then_else(
            None,
            None,
            loop.equal_to(
                loop.load_indirect(
                    "SparseSet",
                    "size",
                    loop.load_indirect("Thread", "set", loop.load("clist")),
                ),
                loop.const_int_32(0),
            ),
        )

        clist_is_empty.call(
            "add",
            8,
            [
                clist_is_empty.const_int_32(0),
                clist_is_empty.load("clist"),
                clist_is_empty.load("pos"),
                clist_is_empty.load("text"),
                clist_is_empty.load("tl"),
                clist_is_empty.load("slots"),
                clist_is_empty.load("sl"),
                clist_is_empty.const_int_32(0),
            ],
        )

        n_is_anchored_start_bldr = n_clist_is_empty.orphan_builder()
        n_is_anchored_start = n_is_anchored_start_bldr.equal_to(
            n_is_anchored_start_bldr.const_int_32(self.prog.anchor_start),
            n_is_anchored_start_bldr.const_int_32(0),
        )
        n_matched_bldr = n_clist_is_empty.orphan_builder()
        n_matched = n_matched_bldr.equal_to(
            n_matched_bldr.load("matched"), n_matched_bldr.const_int_32(0)
        )

        conditions = [
            n_clist_is_empty.make_condition(n_matched_bldr, n_matched),
            n_clist_is_empty.make_condition(
                n_is_anchored_start_bldr, n_is_anchored_start
            ),
        ]

        n_is_anchored_start_n_matched, _ = n_clist_is_empty.if_and(
            None, None, 2, conditions
        )

        n_is_anchored_start_n_matched.call(
            "add",
            8,
            [
                n_is_anchored_start_n_matched.const_int_32(0),
                n_is_anchored_start_n_matched.load("clist"),
                n_is_anchored_start_n_matched.load("pos"),
                n_is_anchored_start_n_matched.load("text"),
                n_is_anchored_start_n_matched.load("tl"),
                n_is_anchored_start_n_matched.load("slots"),
                n_is_anchored_start_n_matched.load("sl"),
                n_is_anchored_start_n_matched.const_int_32(0),
            ],
        )

        clist_iter, clist_iter_break = loop.for_loop_with_break(
            True,
            "idx",
            None,
            None,
            loop.const_int_32(0),
            loop.load_indirect(
                "SparseSet",
                "size",
                loop.load_indirect("Thread", "set", loop.load("clist")),
            ),
            loop.const_int_32(1),
        )

        clist_iter.store(
            "inst_id",
            clist_iter.load_at(
                self.td.p_int_32,
                clist_iter.index_at(
                    self.td.p_int_32,
                    clist_iter.load_indirect(
                        "SparseSet",
                        "dense",
                        clist_iter.load_indirect(
                            "Thread", "set", clist_iter.load("clist")
                        ),
                    ),
                    clist_iter.load("idx"),
                ),
            ),
        )

        matched_builder_2 = clist_iter.if_then(
            None,
            clist_iter.equal_to(
                clist_iter.const_int_32(1),
                clist_iter.call(
                    "step",
                    8,
                    [
                        clist_iter.load("inst_id"),
                        clist_iter.load("nlist"),
                        clist_iter.load("pos"),
                        clist_iter.load("text"),
                        clist_iter.load("tl"),
                        clist_iter.load("slots"),
                        clist_iter.load("sl"),
                        clist_iter.load("clist"),
                    ],
                ),
            ),
        )

        matched_builder_2.store("matched", matched_builder_2.const_int_32(1))
        matched_builder_2.goto(clist_iter_break)

        pos_at_end_bldr = loop.if_then(
            None, loop.greater_or_equal_to(loop.load("pos"), loop.load("tl"))
        )

        pos_at_end_bldr.goto(break_bldr)

        loop.store("pos", loop.add(loop.load("pos"), loop.const_int_32(1)))

        loop.call("swap", 2, [loop.load("nlist"), loop.load("clist")])

        loop.call("clear", 1, [loop.load_indirect("Thread", "set", loop.load("nlist"))])

        self.return_(self.load("matched"))

        return True


class FindAllMethod(jitbuilder.MethodBuilder):
    def __init__(self, td: jitbuilder.TypeDictionary, exec_fn):
        super().__init__(td)
        self.td = td
        self.define_name("find_all")

        # text, tl, slots, sl, ncaps
        self.define_parameter("text", self.td.p_int_8)
        self.define_parameter("tl", self.td.int_32)
        self.define_array_parameter("slots", self.td.p_int_32)
        self.define_parameter("sl", self.td.int_32)
        self.define_parameter("ncaps", self.td.int_32)

        self.define_local("last_match", self.td.int_32)
        self.define_local("last_end", self.td.int_32)
        self.define_local("one", self.td.int_32)

        self.define_local(
            "matches", self.td.pointer_to(self.td.lookup_struct("Matches"))
        )

        self.define_function(
            "exec",
            __file__,
            "NA",
            exec_fn,
            self.td.int_32,
            6,
            [
                self.td.p_int_8,
                self.td.int_32,
                self.td.p_int_32,
                self.td.int_32,
                self.td.int_32,
                self.td.int_32,
            ],
        )

        self.define_function(
            "matches_init",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "matches_init"))),
            self.td.pointer_to(self.td.lookup_struct("Matches")),
            1,
            [self.td.int_32],
        )

        self.define_function(
            "matches_append",
            __file__,
            "NA",
            int(ffi.cast("uintptr_t", ffi.addressof(lib, "matches_append"))),
            self.td.pointer_to(self.td.lookup_struct("Matches")),
            2,
            [self.td.pointer_to(self.td.lookup_struct("Matches")), self.td.int_32],
        )

        self.define_return_type(self.td.pointer_to(self.td.lookup_struct("Matches")))

    def buildIL(self):
        self.all_locals_have_been_defined()

        self.store("last_end", self.const_int_32(0))
        self.store("last_match", self.const_int_32(-1))
        self.store("one", self.const_int_32(1))
        self.store("matches", self.call("matches_init", 1, [self.const_int_32(16)]))

        loop, break_bldr, continue_bldr = self.do_while_loop("one", None, None, None)

        _ = loop.if_then(
            break_bldr, loop.greater_than(loop.load("last_end"), loop.load("tl"))
        )

        match, _ = loop.if_then_else(
            None,
            break_bldr,
            loop.call(
                "exec",
                6,
                [
                    loop.load("text"),
                    loop.load("tl"),
                    loop.load("slots"),
                    loop.load("sl"),
                    loop.load("ncaps"),
                    loop.load("last_end"),
                ],
            ),
        )

        s0_e_s1, n_s0_e_s1 = match.if_then_else(
            None,
            None,
            match.equal_to(
                match.load_at(
                    self.td.p_int_32,
                    match.index_at(
                        self.td.p_int_32, match.load("slots"), match.const_int_32(0)
                    ),
                ),
                match.load_at(
                    self.td.p_int_32,
                    match.index_at(
                        self.td.p_int_32, match.load("slots"), match.const_int_32(1)
                    ),
                ),
            ),
        )

        s0_e_s1.store(
            "last_end",
            s0_e_s1.add(
                s0_e_s1.load_at(
                    self.td.p_int_32,
                    s0_e_s1.index_at(
                        self.td.p_int_32, s0_e_s1.load("slots"), s0_e_s1.const_int_32(1)
                    ),
                ),
                s0_e_s1.const_int_32(1),
            ),
        )

        _ = s0_e_s1.if_then(
            continue_bldr,
            s0_e_s1.equal_to(
                s0_e_s1.load_at(
                    self.td.p_int_32,
                    s0_e_s1.index_at(
                        self.td.p_int_32, s0_e_s1.load("slots"), s0_e_s1.const_int_32(1)
                    ),
                ),
                s0_e_s1.load("last_match"),
            ),
        )

        n_s0_e_s1.store(
            "last_end",
            n_s0_e_s1.load_at(
                self.td.p_int_32,
                n_s0_e_s1.index_at(
                    self.td.p_int_32, n_s0_e_s1.load("slots"), n_s0_e_s1.const_int_32(1)
                ),
            ),
        )

        match.store(
            "last_match",
            match.load_at(
                self.td.p_int_32,
                match.index_at(
                    self.td.p_int_32, match.load("slots"), match.const_int_32(1)
                ),
            ),
        )

        match.call("matches_append", 2, [match.load("matches"), match.load("slots")])

        self.return_(self.load("matches"))

        return True
