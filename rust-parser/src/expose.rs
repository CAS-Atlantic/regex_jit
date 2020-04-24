use re_builder::RegexOptions;

/// Facilitates the construction of an executor by exposing various knobs
/// to control how a regex is executed and what kinds of resources it's
/// permitted to use.
pub struct ExecBuilder {
    options: RegexOptions,
    match_type: Option<MatchType>,
    bytes: bool,
    only_utf8: bool,
}

/// Parsed represents a set of parsed regular expressions and their detected
/// literals.
struct Parsed {
    exprs: Vec<Hir>,
    prefixes: Literals,
    suffixes: Literals,
    bytes: bool,
}

impl ExecBuilder {
    /// Create a regex execution builder.
    ///
    /// This uses default settings for everything except the regex itself,
    /// which must be provided. Further knobs can be set by calling methods,
    /// and then finally, `build` to actually create the executor.
    pub fn new(re: &str) -> Self {
        Self::new_many(&[re])
    }

    /// Like new, but compiles the union of the given regular expressions.
    ///
    /// Note that when compiling 2 or more regular expressions, capture groups
    /// are completely unsupported. (This means both `find` and `captures`
    /// wont work.)
    pub fn new_many<I, S>(res: I) -> Self
    where
        S: AsRef<str>,
        I: IntoIterator<Item = S>,
    {
        let mut opts = RegexOptions::default();
        opts.pats = res.into_iter().map(|s| s.as_ref().to_owned()).collect();
        Self::new_options(opts)
    }

    /// Create a regex execution builder.
    pub fn new_options(opts: RegexOptions) -> Self {
        ExecBuilder {
            options: opts,
            match_type: None,
            bytes: false,
            only_utf8: true,
        }
    }

    /// Set the matching engine to be automatically determined.
    ///
    /// This is the default state and will apply whatever optimizations are
    /// possible, such as running a DFA.
    ///
    /// This overrides whatever was previously set via the `nfa` or
    /// `bounded_backtracking` methods.
    pub fn automatic(mut self) -> Self {
        self.match_type = None;
        self
    }

    /// Sets the matching engine to use the NFA algorithm no matter what
    /// optimizations are possible.
    ///
    /// This overrides whatever was previously set via the `automatic` or
    /// `bounded_backtracking` methods.
    pub fn nfa(mut self) -> Self {
        self.match_type = Some(MatchType::Nfa(MatchNfaType::PikeVM));
        self
    }

    /// Sets the matching engine to use a bounded backtracking engine no
    /// matter what optimizations are possible.
    ///
    /// One must use this with care, since the bounded backtracking engine
    /// uses memory proportion to `len(regex) * len(text)`.
    ///
    /// This overrides whatever was previously set via the `automatic` or
    /// `nfa` methods.
    pub fn bounded_backtracking(mut self) -> Self {
        self.match_type = Some(MatchType::Nfa(MatchNfaType::Backtrack));
        self
    }

    /// Compiles byte based programs for use with the NFA matching engines.
    ///
    /// By default, the NFA engines match on Unicode scalar values. They can
    /// be made to use byte based programs instead. In general, the byte based
    /// programs are slower because of a less efficient encoding of character
    /// classes.
    ///
    /// Note that this does not impact DFA matching engines, which always
    /// execute on bytes.
    pub fn bytes(mut self, yes: bool) -> Self {
        self.bytes = yes;
        self
    }

    /// When disabled, the program compiled may match arbitrary bytes.
    ///
    /// When enabled (the default), all compiled programs exclusively match
    /// valid UTF-8 bytes.
    pub fn only_utf8(mut self, yes: bool) -> Self {
        self.only_utf8 = yes;
        self
    }

    /// Set the Unicode flag.
    pub fn unicode(mut self, yes: bool) -> Self {
        self.options.unicode = yes;
        self
    }

    /// Parse the current set of patterns into their AST and extract literals.
    fn parse(&self) -> Result<Parsed, Error> {
        let mut exprs = Vec::with_capacity(self.options.pats.len());
        let mut prefixes = Some(Literals::empty());
        let mut suffixes = Some(Literals::empty());
        let mut bytes = false;
        let is_set = self.options.pats.len() > 1;
        // If we're compiling a regex set and that set has any anchored
        // expressions, then disable all literal optimizations.
        for pat in &self.options.pats {
            let mut parser = ParserBuilder::new()
                .octal(self.options.octal)
                .case_insensitive(self.options.case_insensitive)
                .multi_line(self.options.multi_line)
                .dot_matches_new_line(self.options.dot_matches_new_line)
                .swap_greed(self.options.swap_greed)
                .ignore_whitespace(self.options.ignore_whitespace)
                .unicode(self.options.unicode)
                .allow_invalid_utf8(!self.only_utf8)
                .nest_limit(self.options.nest_limit)
                .build();
            let expr = parser
                .parse(pat)
                .map_err(|e| Error::Syntax(e.to_string()))?;
            bytes = bytes || !expr.is_always_utf8();

            if cfg!(feature = "perf-literal") {
                if !expr.is_anchored_start() && expr.is_any_anchored_start() {
                    // Partial anchors unfortunately make it hard to use
                    // prefixes, so disable them.
                    prefixes = None;
                } else if is_set && expr.is_anchored_start() {
                    // Regex sets with anchors do not go well with literal
                    // optimizations.
                    prefixes = None;
                }
                prefixes = prefixes.and_then(|mut prefixes| {
                    if !prefixes.union_prefixes(&expr) {
                        None
                    } else {
                        Some(prefixes)
                    }
                });

                if !expr.is_anchored_end() && expr.is_any_anchored_end() {
                    // Partial anchors unfortunately make it hard to use
                    // suffixes, so disable them.
                    suffixes = None;
                } else if is_set && expr.is_anchored_end() {
                    // Regex sets with anchors do not go well with literal
                    // optimizations.
                    suffixes = None;
                }
                suffixes = suffixes.and_then(|mut suffixes| {
                    if !suffixes.union_suffixes(&expr) {
                        None
                    } else {
                        Some(suffixes)
                    }
                });
            }
            exprs.push(expr);
        }
        Ok(Parsed {
            exprs: exprs,
            prefixes: prefixes.unwrap_or_else(Literals::empty),
            suffixes: suffixes.unwrap_or_else(Literals::empty),
            bytes: bytes,
        })
    }

    pub fn instructions(self) -> result::Result<Program, Error> {
        // Special case when we have no patterns to compile.
        // This can happen when compiling a regex set.
        if self.options.pats.is_empty() {
            let ro = Arc::new(ExecReadOnly {
                res: vec![],
                nfa: Program::new(),
                dfa: Program::new(),
                dfa_reverse: Program::new(),
                suffixes: LiteralSearcher::empty(),
                #[cfg(feature = "perf-literal")]
                ac: None,
                match_type: MatchType::Nothing,
            });
            return Ok(Exec {
                ro: ro,
                cache: Cached::new(),
            });
        }
        let parsed = self.parse()?;
        let mut nfa = Compiler::new()
            .size_limit(self.options.size_limit)
            .bytes(self.bytes || parsed.bytes)
            .only_utf8(self.only_utf8)
            .compile(&parsed.exprs)?;
        return nfa;
    }

    /// Build an executor that can run a regular expression.
    pub fn build(self) -> Result<Exec, Error> {
        // Special case when we have no patterns to compile.
        // This can happen when compiling a regex set.
        if self.options.pats.is_empty() {
            let ro = Arc::new(ExecReadOnly {
                res: vec![],
                nfa: Program::new(),
                dfa: Program::new(),
                dfa_reverse: Program::new(),
                suffixes: LiteralSearcher::empty(),
                #[cfg(feature = "perf-literal")]
                ac: None,
                match_type: MatchType::Nothing,
            });
            return Ok(Exec {
                ro: ro,
                cache: Cached::new(),
            });
        }
        let parsed = self.parse()?;
        let mut nfa = Compiler::new()
            .size_limit(self.options.size_limit)
            .bytes(self.bytes || parsed.bytes)
            .only_utf8(self.only_utf8)
            .compile(&parsed.exprs)?;
        let mut dfa = Compiler::new()
            .size_limit(self.options.size_limit)
            .dfa(true)
            .only_utf8(self.only_utf8)
            .compile(&parsed.exprs)?;
        let mut dfa_reverse = Compiler::new()
            .size_limit(self.options.size_limit)
            .dfa(true)
            .only_utf8(self.only_utf8)
            .reverse(true)
            .compile(&parsed.exprs)?;

        #[cfg(feature = "perf-literal")]
        let ac = self.build_aho_corasick(&parsed);
        nfa.prefixes = LiteralSearcher::prefixes(parsed.prefixes);
        dfa.prefixes = nfa.prefixes.clone();
        dfa.dfa_size_limit = self.options.dfa_size_limit;
        dfa_reverse.dfa_size_limit = self.options.dfa_size_limit;

        let mut ro = ExecReadOnly {
            res: self.options.pats,
            nfa: nfa,
            dfa: dfa,
            dfa_reverse: dfa_reverse,
            suffixes: LiteralSearcher::suffixes(parsed.suffixes),
            #[cfg(feature = "perf-literal")]
            ac: ac,
            match_type: MatchType::Nothing,
        };
        ro.match_type = ro.choose_match_type(self.match_type);

        let ro = Arc::new(ro);
        Ok(Exec {
            ro: ro,
            cache: Cached::new(),
        })
    }

    #[cfg(feature = "perf-literal")]
    fn build_aho_corasick(&self, parsed: &Parsed) -> Option<AhoCorasick<u32>> {
        if parsed.exprs.len() != 1 {
            return None;
        }
        let lits = match alternation_literals(&parsed.exprs[0]) {
            None => return None,
            Some(lits) => lits,
        };
        // If we have a small number of literals, then let Teddy handle
        // things (see literal/mod.rs).
        if lits.len() <= 32 {
            return None;
        }
        Some(
            AhoCorasickBuilder::new()
                .match_kind(MatchKind::LeftmostFirst)
                .auto_configure(&lits)
                // We always want this to reduce size, regardless
                // of what auto-configure does.
                .byte_classes(true)
                .build_with_size::<u32, _, _>(&lits)
                // This should never happen because we'd long exceed the
                // compilation limit for regexes first.
                .expect("AC automaton too big"),
        )
    }
}
