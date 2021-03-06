pub use self::imp::*;

mod imp {
    use syntax::hir::literal::Literals;

    #[derive(Clone, Debug)]
    pub struct LiteralSearcher(());

    impl LiteralSearcher {
        pub fn empty() -> Self {
            LiteralSearcher(())
        }

        pub fn prefixes(_: Literals) -> Self {
            LiteralSearcher(())
        }

        pub fn suffixes(_: Literals) -> Self {
            LiteralSearcher(())
        }

        pub fn complete(&self) -> bool {
            false
        }

        pub fn find(&self, _: &[u8]) -> Option<(usize, usize)> {
            unreachable!()
        }

        pub fn find_start(&self, _: &[u8]) -> Option<(usize, usize)> {
            unreachable!()
        }

        pub fn find_end(&self, _: &[u8]) -> Option<(usize, usize)> {
            unreachable!()
        }

        pub fn is_empty(&self) -> bool {
            true
        }

        pub fn len(&self) -> usize {
            0
        }

        pub fn approximate_size(&self) -> usize {
            0
        }
    }
}
