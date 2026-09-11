# Repository working agreement

## Start here

Read README.md and the three current consensus documents before changing the project:

1. docs/context.md — vocabulary, background, resources, and observed state.
2. docs/decisions.md — accepted choices, current scope, and priorities.
3. docs/architecture.md — directory ownership, interfaces, and deployment boundaries.

Then read the relevant recent entries in docs/journal/. User instructions in the
current conversation take precedence over these repository defaults.

## Current phase

The local scaffold is complete. The user has provided a 32 GB NVIDIA cloud
container and authorized deployment, including an eventual one-command testcase
run with visible independent results. Download weights and install GPU dependencies
on the server; keep the workflow and GPU environments separate. Target RTL with
ChipMATE V-4B and P-4B. Reproduce the pinned upstream workflow before changing its
algorithm. The NVIDIA deployment smoke passed three official testcases. The
initial full run completed all 156 tasks with 109 PASS and 47 FAIL, no execution
errors or skipped tasks. A separate CPU reference control found five evaluator
limitations; preserve the raw results and distinguish these from model quality.
Building our own Docker image, Vivado and AMD execution remain later milestones.

## Record every work session

- Create a new docs/journal/YYYYMMDD_HHMMSS_keyword.md entry for each work session,
  using Asia/Shanghai time and an English filename.
- Preserve the user's original requests and the assistant's user-facing responses,
  commands, results, failures, decisions and reasons, outstanding work, and links
  to artifacts. Do not replace historical records with summaries.
- Keep the three consensus documents current; link decisions to their journal
  evidence. Correct old information through a new journal entry.
- Put large raw outputs under a uniquely named runs/ directory and link them.
  Never silently overwrite or automatically delete historical runs.
- Preserve observable evidence and explanations, not private internal reasoning.
  Do not record passwords, tokens, private keys, or authenticated URLs.
- Do not fabricate timestamps, execution results, benchmark scores, or completion.
  Clearly distinguish historical backfill, templates, CPU checks, and GPU runs.

## Engineering boundaries

- Own project code lives in src/qiansai/. Keep GPU dependencies in docker/ and
  serving configuration, accessed through the inference service interface.
- third_party/chipmate and data/verilog_eval are Git submodules pinned by gitlinks.
  Do not update their versions as an incidental side effect of another task.
- Keep the upstream generation workflow unchanged during original reproduction.
- Reference implementations and official testbenches are evaluator inputs.
  Generation inputs may contain the task statement and an interface-only stub.
- Cross-verification agreement is not an independently measured benchmark pass.
- Model weights, virtual environments, caches, and large run artifacts stay outside
  ordinary Git history. Track their identity and relevant results in manifests.
- Use relative repository paths and English filenames. Documentation may be Chinese.
- Keep scripts usable outside Docker as well as inside it.

## Verification and Git

Use pytest for tests, as requested by the user. The smoke script invokes pytest.
Use the smoke check for scaffold changes. Add focused tests only for meaningful
behavior changes. Report skipped GPU/Docker checks explicitly. Review staged files
and submodule revisions before committing. Preserve remote history; never force
push as a routine update. Follow the user's authorization for commits and pushes.
