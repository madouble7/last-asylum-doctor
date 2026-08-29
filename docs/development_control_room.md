# Doctor's Companion Development Control Room

## The operating model

Doctor's Companion has one canonical development repository:

`C:\Users\madou\Documents\last-asylum-doctor`

The normal branch is `main`. ATLAS, SCOUT, and PROBE remain separate specialist
identities and separate Copilot conversations, but their VS Code windows open the
same folder. A change made in the canonical folder is therefore visible to the
other windows without cherry-picking or branch synchronization.

This is an operational concurrency model, not a claim that Git instructions can
prevent conflicts by themselves.

## Three role windows

Each wrapper opens the same canonical folder with a different window title:

- `ATLAS — Doctor's Companion`: implementation and integration.
- `SCOUT — Doctor's Companion`: public-source reconnaissance and evidence.
- `PROBE — Doctor's Companion`: installed-client reconnaissance and safe navigation.

In each window, select the matching custom agent from the Copilot agent picker.

## Ownership

ATLAS normally owns `src/`, `tests/`, database and schema work, the CLI,
integration, optimization, and shared application code.

SCOUT normally owns source reconnaissance, evidence reports, strategy claims,
source lineage, and version research, preferably in Scout-specific docs or
evidence artifacts.

PROBE normally owns `tools/probe*`, `src/last_asylum_doctor/probe/`, PROBE
documentation, client inspection, and specifically assigned perception or
navigation code. Raw probe evidence remains ignored.

All roles may read across the repository. A role may edit another role's default
domain only when the current mission explicitly grants that ownership. If two
roles appear to need the same file, stop editing that file and report the
overlap.

## Concurrent editing rules

During parallel specialist work, agents do not run `git add`, `git commit`,
`git reset`, `git checkout`, `git switch`, `git stash`, `git merge`, or
`git cherry-pick`. This keeps routine work in the shared working tree and avoids
manual synchronization by Matt.

When a sprint is complete, Matt explicitly designates ATLAS as `INTEGRATOR`.
The integrator then:

1. Inspects every working-tree change.
2. Checks for unexpected file or domain overlap.
3. Runs the focused checks and broader tests appropriate to the changes.
4. Reconciles only explicitly authorized shared changes.
5. Commits one coherent checkpoint to `main`.

## Launching the control room

From the canonical repository, run one command:

```powershell
.\scripts\open-control-room.ps1
```

The launcher opens three independent VS Code windows with the `Last Asylum
Doctor` profile. To inspect the commands without opening windows:

```powershell
.\scripts\open-control-room.ps1 -DryRun
```

Each workspace sets terminal cwd to the canonical workspace folder, selects a
workspace-local `Doctor PowerShell` profile using
`C:\Program Files\PowerShell\7\pwsh.exe`, and points Python at
`.venv\Scripts\python.exe`. The profile has no startup arguments and does not
change directory to `C:\kortana`; the workspace cwd supplies the repo location.

## Safety and settings

The workspace wrappers use supported VS Code settings for window titles,
terminal cwd, and the Python interpreter. They do not enable global tool
auto-approval, dangerous permission bypass, or uncontrolled autopilot behavior.

Global VS Code approval and execution settings are not safely or reliably
overridden here because their exact behavior depends on the installed VS Code
and Copilot versions and user profile. Keep those settings conservative. PROBE's
account-state-changing actions must remain prohibited by deterministic execution
allowlists in code, regardless of Copilot settings.

## If two agents touch one file

Stop both edits to that file. Do not reset, stash, checkout, merge, or cherry-pick
to make the working tree look clean. Tell Matt which roles touched it and ask
ATLAS, explicitly designated as `INTEGRATOR`, to inspect the competing changes.
The integrator compares intent and evidence, keeps only authorized changes,
runs the relevant checks, and records the resolution in the next checkpoint.

## Legacy worktrees

These temporary recovery and archive copies are intentionally retained:

- `C:\Users\madou\Documents\last-asylum-doctor-source-intel`
- `C:\Users\madou\Documents\last-asylum-doctor-probe`

They are not part of the normal workflow, are not reset or merged by this
change, and should not receive routine edits. They can be retired separately
after the shared-main control room has been proven stable.