extern crate aho_corasick;
extern crate pyo3;
extern crate regex_syntax as syntax;

mod compile;
mod dfa;
mod error;
mod expand;
mod find_byte;
mod input;
mod literal;
mod pikevm;
mod prog;
mod re_builder;
mod re_bytes;
mod re_unicode;
mod sparse;
mod utf8;
// mod pattern;
mod backtrack;
mod cache;
mod exec;
mod re_set;
mod re_trait;

// use exec::ExecBuilder;

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

use prog::{Inst, Program};

use exec::ExecBuilder;

#[pyclass]
#[derive(Clone, Debug, Default)]
struct Instruction {
    #[pyo3(get)]
    match_id: usize,
    #[pyo3(get)]
    goto: usize,
    #[pyo3(get)]
    slot: usize,
    #[pyo3(get)]
    alternate_goto: usize,
    #[pyo3(get)]
    look: String,
    #[pyo3(get)]
    start: u8,
    #[pyo3(get)]
    end: u8,
    #[pyo3(get)]
    kind: String,
    #[pyo3(get)]
    ch: String,
    ranges: Vec<(String, String)>,
}

#[pyfunction]
fn compile_regex(regex: &str) -> PyResult<RegexProgram> {
    let prog = ExecBuilder::new(regex).nfa_program().unwrap();
    let py_prog = RegexProgram {
        instructions: simplify_instructions(prog.insts),
        start: prog.start,
        is_anchored_start: prog.is_anchored_start,
        is_anchored_end: prog.is_anchored_end,
        has_unicode_word_boundary: prog.has_unicode_word_boundary,
    };
    Ok(py_prog)
}

#[pyfunction]
fn dump_bytecode(regex: &str) -> PyResult<String> {
    let prog = ExecBuilder::new(regex).nfa_program().unwrap();
    Ok(format!("{:?}", prog))
}

fn simplify_ranges(ranges: Vec<(char, char)>) -> Vec<(String, String)> {
    let mut v = vec![];
    for r in ranges {
        v.push((r.0.to_string(), r.1.to_string()))
    }
    v
}

fn simplify_instructions(insts: Vec<Inst>) -> Vec<Instruction> {
    let mut v = vec![];
    for inst in insts {
        match inst {
            Inst::Match(id) => v.push(Instruction {
                match_id: id,
                kind: "match".to_string(),
                ..Default::default()
            }),
            Inst::Bytes(bytes_inst) => v.push(Instruction {
                goto: bytes_inst.goto,
                start: bytes_inst.start,
                end: bytes_inst.end,
                kind: "bytes".to_string(),
                ..Default::default()
            }),
            Inst::Save(save_inst) => v.push(Instruction {
                goto: save_inst.goto,
                slot: save_inst.slot,
                kind: "save".to_string(),
                ..Default::default()
            }),
            Inst::Split(split_inst) => v.push(Instruction {
                goto: split_inst.goto1,
                alternate_goto: split_inst.goto2,
                kind: "split".to_string(),
                ..Default::default()
            }),
            Inst::Ranges(ranges_inst) => v.push(Instruction {
                goto: ranges_inst.goto,
                kind: "ranges".to_string(),
                ranges: simplify_ranges(ranges_inst.ranges),
                ..Default::default()
            }),
            Inst::Char(char_inst) => v.push(Instruction {
                goto: char_inst.goto,
                ch: char_inst.c.to_string(),
                kind: "char".to_string(),
                ..Default::default()
            }),
            Inst::EmptyLook(empty_inst) => v.push(Instruction {
                goto: empty_inst.goto,
                kind: format!("{:?}", empty_inst.look),
                ..Default::default()
            }),
        }
    }
    v
}

#[pyclass]
struct RegexProgram {
    instructions: Vec<Instruction>,
    start: usize,
    is_anchored_start: bool,
    is_anchored_end: bool,
    has_unicode_word_boundary: bool,
}

#[pymethods]
impl RegexProgram {
    #[getter]
    fn instructions(&self) -> PyResult<Vec<Instruction>> {
        Ok(self.instructions.clone())
    }
    #[getter]
    fn start(&self) -> PyResult<usize> {
        Ok(self.start)
    }
    #[getter]
    fn is_anchored_start(&self) -> PyResult<bool> {
        Ok(self.is_anchored_start)
    }
    #[getter]
    fn is_anchored_end(&self) -> PyResult<bool> {
        Ok(self.is_anchored_end)
    }
    #[getter]
    fn has_unicode_word_boundary(&self) -> PyResult<bool> {
        Ok(self.has_unicode_word_boundary)
    }
}

/// This module is a python module implemented in Rust.
#[pymodule]
fn regexcompiler(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(compile_regex))?;
    m.add_wrapped(wrap_pyfunction!(dump_bytecode))?;

    Ok(())
}
