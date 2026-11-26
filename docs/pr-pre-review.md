# Pre-review checklist for pull requests

Run this pass before a pull request is opened for review, or moved out of
draft, in the workspace or in any repository under `repos/`. It does the
checks a maintainer's review does: the change fits the architecture, it
compiles, and the pull request's own claims hold. Problems are then found
before a reviewer spends time on them.

The result is a written report for the author. The author reads it and
decides what to fix and what goes into the pull request. An agent does not
post the report, or comments from it, to the pull request unless the author
asks.

`docs/agent-test-policy.md` still decides which tests a change needs. This
checklist decides how a finished pull request is checked.

## 1. Identify the pull request and its state

- Read the pull request's description in full: its summary, its testing
  section, and any "depends on" or "merge after" notes.
- Check the remotes before comparing branches. In some checkouts `origin` is
  the author's fork and `upstream` is the `fujinet-nio/` repository. Compare
  against the repository the pull request targets.
- Confirm every pull request it depends on is merged. Note any that are still
  open, and the order the pull requests must merge in (see step 6).
- Confirm the branch is rebased on the current target branch, so the diff
  holds only this pull request's commits.
- Record the CI result and whether GitHub reports the pull request as
  mergeable.

## 2. Read the architecture that governs the change

Read the docs that own the changed area before reading the code:

- The `AGENTS.md` of the workspace and of each repository touched.
- The architecture docs for the area. For example, `docs/amiga/` (broker,
  DiskDevice and media, RS-232 handshake, CLI stack and `IORequest` rules),
  and the repository's own `docs/` and design specs.
- Any design spec the pull request names, then check that the code does what
  the spec says.

Report each place where the change departs from a documented contract, or
where a doc the change affects was not updated.

## 3. Build it from a clean checkout

- Check the branch out into a separate worktree or a clean tree, never on top
  of the author's working copy.
- Build every target the change touches, with the workspace environment
  (`source "$NIO_WORKSPACE/scripts/env.sh"`). Use the repository's own entry
  points (`make check` for `fujinet-nio-lib`, `make amiga
  AMIGA_PROFILE=<profile>` for nio-config, `scripts/amiga-artifacts
  <profile>` for workspace packaging, and so on).
- Record every warning the change introduces. A warning that was already
  there is noted as pre-existing, not counted against the change.
- A failed build has to be explained before it is reported. A stale build
  directory, for example dependency files left by a build of another branch,
  is an environment problem, not a defect in the change. Move the stale
  directory aside and build again.
- If a toolchain, licensed media or hardware is missing, record exactly which
  target could not be built and why. Do not substitute an unrelated build.

Worktree notes:

- A worktree outside the workspace does not find its sibling repositories by
  relative path. Pass them explicitly, for example
  `FUJINET_NIO_LIB=$NIO_WORKSPACE/repos/fujinet-nio-lib` and
  `FUJINET_NIO_DRIVER=$NIO_WORKSPACE/repos/fujinet-nio-driver`.
- Build against the dependency versions the pull request will merge with,
  usually the target branch of each dependency, as CI does.

## 4. Run the tests

- Run the tests the pull request's testing section names, and the gate that
  `docs/agent-test-policy.md` sets for each repository touched.
- Compare the results with what the description claims, for example the
  number of checks that pass.
- Note any behaviour the change adds that no test covers. When the gap is
  cheap to close, check the behaviour directly: a small host harness with the
  OS calls stubbed is often enough for C code that only runs on the target.

## 5. Check every claim in the description

Go through the summary and the testing section line by line. Mark each claim:

- **Verified:** checked in this pass. Say how.
- **Not verified:** could be checked, but was not. Say why.
- **Cannot verify here:** needs hardware, licensed media or a person, for
  example a test on a real machine. Say what would verify it.

A claim that turns out to be false is a finding.

## 6. Read the code for bugs

Read the diff for correctness, not style. Look in particular at:

- Error, timeout, cancel and revert paths, and what state each one leaves
  behind on both ends of a link.
- Anything that writes user files or startup files: what happens if it is
  interrupted, and whether it can overwrite what it promises to keep.
- Platform limits that apply: for Amiga, Kickstart 1.3 (V33) calls only where
  1.3 is supported, CLI stack size, and `IORequest` ownership.
- Buffer sizes and string lengths at their largest inputs.
- How the change interacts with the pull requests it depends on, or that
  depend on it. A file that one pull request expects and another produces
  means the two must merge in a set order, or together.

## 7. Add the author's own checks

Ask the author for anything else to validate, and add it to the pass.

## 8. Write the report

One report per pull request, in this order:

1. **Verdict:** ready for review, ready with notes, or not ready.
2. **State:** dependencies, rebase, CI, mergeability.
3. **Builds and tests:** each command run and its result, with warning counts.
4. **Claims:** each claim from the description and its mark from step 5.
5. **Findings:** most severe first. Give each one the file and line, what is
   wrong, and a concrete case where it goes wrong. Keep pre-existing problems
   separate from problems the change adds.
6. **Not checked:** anything this pass could not cover, and why.

Keep the report factual. Do not post it to the pull request; the author
decides what to use.
