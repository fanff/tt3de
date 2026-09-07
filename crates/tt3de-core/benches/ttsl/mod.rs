//! TTSL execution benchmarks.
//!
//! Kept in a subdirectory so Cargo does not auto-discover `exec.rs` as a
//! standalone bench target; both files are modules of the `all` harness.

pub mod exec;
pub mod fixtures;
