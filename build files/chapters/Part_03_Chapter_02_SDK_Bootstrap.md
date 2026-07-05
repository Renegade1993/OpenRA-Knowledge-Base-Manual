# Chapter 3.2 — Mod SDK Bootstrapping

## Purpose

The OpenRA [Mod SDK](../appendices/Appendix_A_Glossary.md) bootstrapping layer is the small set of cross-platform entry scripts and configuration files that turn a standalone [mod](../appendices/Appendix_A_Glossary.md) repository into a runnable game. Its responsibilities are narrow but critical: declare which mod and which engine version the project needs, acquire and pin that engine version automatically, resolve the correct .NET runtime, and hand control over to the engine with the right command-line arguments. By keeping mod assets, custom C# code, and engine binaries in separate, well-defined locations, the bootstrap scripts enforce the OpenRA design philosophy that a mod is a *consumer* of the engine, not a fork of it.

This chapter documents the bootstrap flow from the moment a developer types `launch-game.sh` (Linux/macOS) or `launch-game.cmd` (Windows) through the automatic engine download and build orchestration performed by `make`/`make.cmd`/`make.ps1`.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the role of the Mod SDK bootstrap layer in keeping mods and engine separate.
- Configure mod.config and user.config for engine version, mod ID, and directory layout.
- Trace the launch flow from launch-game.sh/cmd through engine version checks to OpenRA execution.
- Describe how make/Makefile/make.ps1 fetch and build the pinned engine.
- Identify the cross-platform differences between Unix and Windows bootstrap scripts.
- Debug common bootstrap failures such as missing engine or runtime mismatch.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRAModSDK/mod.config` | Central key-value configuration file defining the mod identity, required engine version, download source, and local directory layout. |
| `OpenRAModSDK/user.config` | Optional, uncommitted override file read after `mod.config`; allows per-developer overrides without editing the tracked file. |
<!-- DEV-NOTE [tooling]: Microsoft .NET SDK: https://dotnet.microsoft.com — required to build the OpenRA engine and mod projects. -->
| `OpenRAModSDK/launch-game.sh` | Unix launcher entry point. Validates tools, sources the config files, checks the engine, picks `mono` or `dotnet`, and runs `OpenRA.dll`. |
| `OpenRAModSDK/launch-game.cmd` | Windows launcher entry point. Parses config files, validates required variables, checks the engine, and runs `OpenRA.exe`. |
| `OpenRAModSDK/fetch-engine.sh` | Unix helper that downloads, extracts, and compiles the engine if the local copy is missing or out of date. |
| `OpenRAModSDK/Makefile` | Unix build orchestrator. Exposes targets such as `all`, `engine`, `clean`, `version`, `test`, `check`, and `check-scripts`. |
| `OpenRAModSDK/make.cmd` | Thin Windows wrapper that simply forwards its arguments to `make.ps1` via PowerShell. |
| `OpenRAModSDK/make.ps1` | Windows build orchestrator. Mirrors the Unix `Makefile` targets, fetches the engine if needed, and compiles the mod. |

![Architecture diagram](images/Part_03_Chapter_02_SDK_Bootstrap-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


At the highest level, the Mod SDK is a **dependency manager plus launcher wrapper**. The mod repository contains only the pieces that belong to the [mod](../appendices/Appendix_A_Glossary.md): a `mods/` directory, optional custom `.sln` / `.csproj` files, packaging scripts, documentation, and a few small bootstrap files. The [engine](../appendices/Appendix_A_Glossary.md) itself is treated as an external, pinned dependency, downloaded into a local directory that is normally excluded from version control.

![Architecture](images/Part_03_Chapter_02_SDK_Bootstrap-Architecture.svg)

The launcher scripts live *inside* the mod repository, but they run the engine binary that lives *inside* the engine directory. This separation is the core of the decoupling: a mod repository does not need to contain the engine source, only a pointer to a precise engine version.

### Separation of concerns

| Concern | Lives in mod repo | Lives in engine directory | Lives in config |
| :---- | :---- | :---- | :---- |
| Gameplay rules, art, maps, audio | `mods/` | — | — |
| Custom C# logic | `*.sln` / `*.csproj` | — | — |
| Engine version selection | — | — | `ENGINE_VERSION` |
| Mod identity | — | — | `MOD_ID` |
| Engine binaries | — | `bin/OpenRA.dll` | — |
| Engine source / build system | — | engine root | — |
| Local engine path | — | — | `ENGINE_DIRECTORY` |

Because the engine is downloaded and built locally, the same mod repository can be checked out by any developer on Linux, macOS, or Windows, and the bootstrap scripts will produce a runnable environment for that platform.

![Data flow  code path diagram](images/Part_03_Chapter_02_SDK_Bootstrap-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### 1. Launcher entry point

A developer invokes the mod with either `launch-game.sh` (Unix) or `launch-game.cmd` (Windows). The two scripts are not shared code; they are platform-specific implementations of the same contract.

#### `launch-game.sh` (Unix)

1. **Prerequisite check**: the script verifies that at least one of `mono` or `dotnet` is installed, and that either `python3` or `python` is available.
2. **Locate the SDK root**: `python` is used to resolve the real path of the script, from which the `TEMPLATE_ROOT` and the mod search path are derived.
3. **Load configuration**: `mod.config` is sourced as a shell script; `user.config` is sourced if it exists. Because the config file is written as `KEY="value"`, sourcing it directly sets shell variables.
4. **Validate required variables**: a helper `require_variables` asserts that `MOD_ID`, `ENGINE_VERSION`, and `ENGINE_DIRECTORY` are non-empty.
5. **Engine version check**: the script verifies that `${ENGINE_DIRECTORY}/bin/OpenRA.dll` exists and that the contents of `${ENGINE_DIRECTORY}/VERSION` exactly match `ENGINE_VERSION`. If either test fails, it prints an error and exits with the message to run `make`.
6. **Runtime selection**: if `mono` is installed and `OpenRA.dll` does not contain the string `.NETCoreApp,Version=`, the launcher chooses `mono --debug`; otherwise it chooses `dotnet`.
7. **Handoff to engine**: the working directory changes to the engine directory and the engine is launched with the arguments `Game.Mod="${MOD_ID}"`, `Engine.EngineDir=".."`, `Engine.LaunchPath="${TEMPLATE_LAUNCHER}"`, and `Engine.ModSearchPaths="${MOD_SEARCH_PATHS}"`, plus any extra arguments passed through `$@`.

#### `launch-game.cmd` (Windows)

1. **Parse configuration**: the batch file iterates over `mod.config` and `user.config` (if present), splitting each line at the first `=` and assigning the left side as an environment variable and the right side as its value.
2. **Validate required variables**: it checks `MOD_ID`, `ENGINE_VERSION`, and `ENGINE_DIRECTORY`.
3. **Engine presence and version check**: it verifies that `%ENGINE_DIRECTORY%\bin\OpenRA.exe` exists and that the string `%ENGINE_VERSION%` appears in `%ENGINE_DIRECTORY%\VERSION`.
4. **Launch**: after changing to the engine directory, it runs `bin\OpenRA.exe` with the same argument set as the Unix launcher.
5. **Error handling**: if the engine exits with a non-zero code, the script shows a crash dialog pointing the user to the logs and FAQ.

### 2. Build entry point (Unix)

When a developer runs `make` or `make all`:

1. `Makefile` sets defaults: `RUNTIME ?= net6`, `CONFIGURATION ?= Release`.
2. It detects the host platform (`linux-x64`, `linux-arm64`, `osx-x64`, `osx-arm64`, or `unix-generic`) unless `TARGETPLATFORM` is already provided.
3. `all` depends on `engine`.
4. `engine` depends on `check-variables` and `check-sdk-scripts`.
5. `fetch-engine.sh` is invoked. If the engine is already present and its `VERSION` matches `ENGINE_VERSION`, it exits immediately; otherwise it downloads the archive, extracts it, removes a lint file that the example mod cannot pass, and runs the engine's own `make version`.
6. The engine is then built with `make RUNTIME=$(RUNTIME) TARGETPLATFORM=$(TARGETPLATFORM) all`.
7. Finally, the mod's own `.sln` files (if any) are compiled with `dotnet build` or `msbuild`, depending on the runtime.

### 3. Build entry point (Windows)

When a developer runs `make.cmd` or `make all` on Windows:

1. `make.cmd` calls `make.ps1` with all arguments forwarded.
2. `make.ps1` requires PowerShell 3 or later.
3. It parses `mod.config` and `user.config` using `ReadConfigLine` / `ParseConfigFile`, which populates environment variables for a fixed set of keys.
4. If the command is `all`, `clean`, or `check`, it inspects the engine version.
   - If the engine is present and matches `ENGINE_VERSION`, it delegates to the engine's own `make.cmd` inside the engine directory.
   - If `AUTOMATIC_ENGINE_MANAGEMENT` is disabled, it stops with a manual-update message.
   - Otherwise, it deletes the old engine directory, downloads the zip from `AUTOMATIC_ENGINE_SOURCE`, extracts it, renames the extracted folder to `ENGINE_DIRECTORY`, removes the same lint file, and runs the engine's `make.cmd version` and `make.cmd $command`.
5. It sets `$utilityPath = $env:ENGINE_DIRECTORY + "/bin/OpenRA.Utility.exe"`.
6. It dispatches to the command handler (`All-Command`, `Clean-Command`, `Version-Command`, `Test-Command`, `Check-Command`, or `Check-Scripts-Command`).

![Configuration (yaml) diagram](images/Part_03_Chapter_02_SDK_Bootstrap-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


`mod.config` is not MiniYAML; it is a plain `KEY="value"` file read as shell-style variables. However, it is the single source of truth for all bootstrap behavior, and it is the closest equivalent to a YAML manifest for this layer.

### Core variables

| Variable | Default example | Meaning |
| :---- | :---- | :---- |
| `MOD_ID` | `"example"` | The directory name under `mods/` that contains the mod's `mod.yaml`. The engine will load `mods/$MOD_ID/mod.yaml`. Must not contain spaces. |
| `ENGINE_VERSION` | `"release-20250330"` | The exact OpenRA engine version required by this mod. This is the version string written into the engine's `VERSION` file and used as the Git ref / archive tag for downloads. |
| `ENGINE_DIRECTORY` | `"./engine"` | The local path (relative to the SDK root) where the engine source/binaries are stored. |

### Engine management variables

| Variable | Default example | Meaning |
| :---- | :---- | :---- |
| `AUTOMATIC_ENGINE_MANAGEMENT` | `"True"` | When `True`, the SDK is allowed to download and replace the engine directory automatically. When `False`, the developer must manage the engine manually. |
| `AUTOMATIC_ENGINE_SOURCE` | `"https://github.com/OpenRA/OpenRA/archive/${ENGINE_VERSION}.zip"` | The URL from which the engine archive is downloaded. The literal substring `${ENGINE_VERSION}` is replaced by the value of `ENGINE_VERSION`. |
| `AUTOMATIC_ENGINE_EXTRACT_DIRECTORY` | `"./engine_temp"` | Temporary directory used while extracting the downloaded archive. |
| `AUTOMATIC_ENGINE_TEMP_ARCHIVE_NAME` | `"engine.zip"` | File name for the downloaded archive. |

### Packaging variables (read by build/packaging scripts)

The file also contains many packaging keys (`PACKAGING_INSTALLER_NAME`, `PACKAGING_DISPLAY_NAME`, `PACKAGING_WEBSITE_URL`, `PACKAGING_FAQ_URL`, `PACKAGING_AUTHORS`, `PACKAGING_COPY_CNC_DLL`, `PACKAGING_COPY_D2K_DLL`, etc.). These are not used by the bootstrap launcher itself, but they are part of the same config contract because the packaging scripts read the same `mod.config` file.

### `user.config` overrides

Both the Unix and Windows bootstrap paths read `user.config` after `mod.config` if it exists. This allows a developer to override `ENGINE_VERSION`, `ENGINE_DIRECTORY`, or any other key locally without changing the committed file. The order of precedence is:

1. `mod.config` (shared defaults).
2. `user.config` (per-user overrides).

Any values not present in `user.config` retain the value from `mod.config`.

## Interconnectivity

- **Depends on:**
  - The OpenRA engine repository (`OpenRA/OpenRA`), because the bootstrap downloads and builds the engine from it.
  - The engine's own `Makefile` and `make.cmd` inside the engine directory, which are invoked to build the engine and stamp its version.
  - The mod's `mods/<MOD_ID>/mod.yaml`, which is not read by the bootstrap scripts but is passed to the engine as the mod manifest to load.
- **Used by:**
  - The packaging scripts in `packaging/` (Linux, macOS, Windows), which read the same `mod.config` variables to produce installers.
  - The dedicated-server launcher (`launch-dedicated.sh`), which follows the same config-loading and runtime-resolution pattern.
  - The utility script (`utility.sh` / `utility.cmd`), which is used by the `test` and `check` make targets.

![Algorithms diagram](images/Part_03_Chapter_02_SDK_Bootstrap-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Required-variable validation

Both `launch-game.sh` and `fetch-engine.sh` use the same `require_variables` function:

```
for each variable name in [MOD_ID, ENGINE_VERSION, ENGINE_DIRECTORY]:
    if the variable is empty or unset:
        append the variable name to the missing list
if the missing list is not empty:
    print "Required mod.config variables are missing:" and the list
    exit with failure
```

The Windows launcher uses a simpler inline check: if `!MOD_ID!`, `!ENGINE_VERSION!`, or `!ENGINE_DIRECTORY!` is empty after parsing, it jumps to the `badconfig` label. `make.ps1` collects missing variables into a `$missing` array and prints the same diagnostic before exiting.

### Runtime selection (Unix)

```
if mono is available:
    if OpenRA.dll does not contain the string ".NETCoreApp,Version=":
        RUNTIME_LAUNCHER = "mono --debug"
    else:
        RUNTIME_LAUNCHER = "dotnet"
else if dotnet is available:
    RUNTIME_LAUNCHER = "dotnet"
else:
    error: "The OpenRA mod SDK requires dotnet or mono."
```

The check for `.NETCoreApp,Version=` inside the assembly is a heuristic: if the engine was built for .NET Core / .NET 5+, it needs `dotnet`; otherwise it is a .NET Framework / Mono build and can be run with `mono`. The Windows launcher does not perform this check because the Windows distribution of the SDK always expects `OpenRA.exe` and .NET 6+.

### Engine version pinning

The engine version is pinned by the `VERSION` file placed inside the engine directory. The bootstrap scripts compare this file to the value of `ENGINE_VERSION` from `mod.config`.

Unix:
```
if OpenRA.dll does not exist or (cat ENGINE_DIRECTORY/VERSION) != ENGINE_VERSION:
    print "Required engine files not found."
    exit with failure
```

Windows:
```
if OpenRA.exe does not exist or ENGINE_VERSION not found in ENGINE_DIRECTORY/VERSION:
    print "Required engine files not found."
    pause and exit
```

When `make` or `make.ps1` updates the engine, it stamps the engine with `make version VERSION="<ENGINE_VERSION>"`, which writes the version into the engine's `VERSION` file.

### Automatic engine fetch (Unix)

```
if AUTOMATIC_ENGINE_MANAGEMENT is not "True":
    error and ask for manual update

if current engine VERSION == ENGINE_VERSION:
    exit 0

if engine directory exists:
    print current version (or "unknown version")
    delete engine directory

print "Downloading engine..."
if curl available:
    download using curl -L -O
else:
    download using wget -cq

extract archive
inspect top-level directory name in the zip (REFNAME)
move engine_temp/REFNAME to ENGINE_DIRECTORY
remove engine_temp and archive
remove OpenRA.Mods.Common/Lint/CheckFluentReferences.cs
change to ENGINE_DIRECTORY
run "make version VERSION=ENGINE_VERSION"
```

The removal of `CheckFluentReferences.cs` is a deliberate hack: the SDK ships with an example mod that does not satisfy that lint check, so the file is deleted to prevent a false failure during the engine build.

### Automatic engine fetch (Windows)

The Windows path in `make.ps1` is conceptually identical but uses .NET APIs:

```
if current engine VERSION == ENGINE_VERSION:
    delegate to engine's make.cmd

if AUTOMATIC_ENGINE_MANAGEMENT != "True":
    error and ask for manual update

if engine directory exists:
    delete it

print "Downloading engine..."
remove old temp extract directory
construct URL by replacing ${ENGINE_VERSION} in AUTOMATIC_ENGINE_SOURCE
System.Net.WebClient.DownloadFile(url, tempArchive)
System.IO.Compression.ZipFile.ExtractToDirectory(tempArchive, tempExtractDir)
move extracted subdir to ENGINE_DIRECTORY
remove temp extract directory and archive
remove OpenRA.Mods.Common/Lint/CheckFluentReferences.cs
delegate to engine's make.cmd version and make.cmd <command>
```

### Build orchestration

Unix `Makefile`:

```
engine target:
    run fetch-engine.sh
    run engine make with RUNTIME and TARGETPLATFORM

all target:
    depend on engine
    if RUNTIME == mono:
        msbuild each .sln with Mono=true
    else:
        dotnet build each .sln

clean target:
    depend on engine
    clean each .sln
    clean engine

version target:
    call engine packaging function to set mod.yaml version

test target:
    depend on all
    run utility.sh --check-yaml

check target:
    depend on engine
    build in Debug with warnings as errors
    run utility.sh --check-explicit-interfaces
    run utility.sh --check-conditional-trait-interface-overrides
```

Windows `make.ps1`:

```
parse mod.config and user.config
if command is all/clean/check:
    fetch or verify engine
    run engine's make.cmd for the same command
set utilityPath = ENGINE_DIRECTORY/bin/OpenRA.Utility.exe
if command is all:
    All-Command: dotnet build *.sln
if command is clean:
    Clean-Command: dotnet clean, remove obj directories
if command is version:
    Version-Command: edit mods/<MOD_ID>/mod.yaml
if command is test:
    Test-Command: [Utility](../appendices/Appendix_A_Glossary.md).exe --check-[yaml](../appendices/Appendix_A_Glossary.md)
if command is check:
    Check-Command: build debug with warnaserror, then utility checks
if command is check-scripts:
    Check-Scripts-Command: luac -p each .lua map script
```

![Extension points diagram](images/Part_03_Chapter_02_SDK_Bootstrap-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


- **Custom engine directory:** a developer can set `ENGINE_DIRECTORY` to a different path in `user.config` to point to a manually built engine. This is useful when testing engine changes alongside the mod.
- **Custom engine source:** `AUTOMATIC_ENGINE_SOURCE` can be changed to point to a fork or a private archive. The only requirement is that the archive must contain a single top-level directory that the extraction scripts can rename.
- **Manual engine management:** set `AUTOMATIC_ENGINE_MANAGEMENT="False"` and the SDK will stop trying to download the engine. The developer must then place the correct engine at `ENGINE_DIRECTORY` and run the engine's own build.
- **Custom build targets:** `Makefile` and `make.ps1` can be extended with new targets for mod-specific tools, but doing so requires keeping both Unix and Windows scripts in sync.
- **Additional packaging metadata:** the packaging variables in `mod.config` are read directly by the packaging scripts, so adding new installer behavior usually starts with adding a new config key.

![Common pitfalls  guardrails diagram](images/Part_03_Chapter_02_SDK_Bootstrap-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Line endings in `mod.config`:** `Makefile` has a `check-sdk-scripts` target that runs `awk '/\r$/ { exit(1); }' mod.config`. If `mod.config` is saved with CRLF line endings, the Unix shell scripts will fail to parse it correctly. The file must use Unix line endings (LF).

- **Executable bit on shell scripts:** `check-sdk-scripts` also verifies that `fetch-engine.sh`, `launch-dedicated.sh`, `launch-game.sh`, and `utility.sh` are executable. If the SDK is cloned on Windows or extracted from an archive, the executable bits may be lost. Run `git update-index --chmod=+x *.sh` and commit the resulting mode change.

- **Missing engine version error:** if `launch-game.sh` prints `Required engine files not found`, the root cause is almost always that the `VERSION` file inside the engine directory does not match `ENGINE_VERSION` in `mod.config`, or that the engine was never built. Running `make` resolves this.

- **Runtime mismatch:** on Unix, if both `mono` and `dotnet` are installed, the launcher chooses based on whether the built engine assembly contains `.NETCoreApp,Version=`. If the engine is rebuilt for a different framework without updating the launcher, the wrong runtime may be selected. Keep the engine and SDK versions in sync.

- **Windows batch parser limitations:** `launch-game.cmd` splits each config line at the first `=` only. Values that themselves contain `=` will be truncated. Avoid `=` in config values.

- **PowerShell execution policy:** `make.cmd` passes `-ExecutionPolicy Bypass` to PowerShell, so the script can run even if the default policy is restricted. Do not remove this flag unless the environment is already configured to allow unsigned scripts.

- **Engine archive top-level directory:** `fetch-engine.sh` assumes the downloaded zip has exactly one top-level directory (e.g., `OpenRA-release-20250330`). The Windows script uses `Get-ChildItem -Recurse | Select-Object -First 1` for the same assumption. Custom archives must follow this layout.

- **The `CheckFluentReferences.cs` hack:** the SDK removes `OpenRA.Mods.Common/Lint/CheckFluentReferences.cs` from the downloaded engine. If the engine's lint checks change, this removal may break the engine build or become unnecessary. It exists only for the example mod; production mods should not rely on it being removed.

- **Do not commit the engine directory:** `ENGINE_DIRECTORY` and `AUTOMATIC_ENGINE_EXTRACT_DIRECTORY` are intended to be temporary. Add them to `.gitignore` so the pinned engine is not committed.

- **Mod search paths:** the launcher passes `Engine.ModSearchPaths="./mods,<engine>/mods"` (Windows) or `${TEMPLATE_ROOT}/mods,./mods` (Unix). The engine then scans those directories for a subdirectory matching `MOD_ID`. If the mod is not found, the engine will fail to start; the path must be correct relative to the engine directory.

## Summary

This chapter explains how the OpenRA [Mod SDK](../appendices/Appendix_A_Glossary.md) bootstrapping layer turns a standalone [mod](../appendices/Appendix_A_Glossary.md) repository into a runnable game.

After reading this chapter, you should be able to:

- **Prerequisite check**: the script verifies that at least one of `mono` or `dotnet` is installed, and that either `python3` or `python` is available.
- **Locate the SDK root**: `python` is used to resolve the real path of the script, from which the `TEMPLATE_ROOT` and the mod search path are derived.
- **Load configuration**: `mod.config` is sourced as a shell script; `user.config` is sourced if it exists. Because the config file is written as `KEY="value"`, sourcing it directly sets shell variables.
- **Validate required variables**: a helper `require_variables` asserts that `MOD_ID`, `ENGINE_VERSION`, and `ENGINE_DIRECTORY` are non-empty.
- **Engine version check**: the script verifies that `${ENGINE_DIRECTORY}/bin/OpenRA.dll` exists and that the contents of `${ENGINE_DIRECTORY}/VERSION` exactly match `ENGINE_VERSION`. If either test fails, it prints an error and exits with the message to run `make`.
- **Runtime selection**: if `mono` is installed and `OpenRA.dll` does not contain the string `.NETCoreApp,Version=`, the launcher chooses `mono --debug`; otherwise it chooses `dotnet`.
- **Handoff to engine**: the working directory changes to the engine directory and the engine is launched with the arguments `Game.Mod="${MOD_ID}"`, `Engine.EngineDir=".."`, `Engine.LaunchPath="${TEMPLATE_LAUNCHER}"`, and `Engine.ModSearchPaths="${MOD_SEARCH_PATHS}"`, plus any extra arguments passed through `$@`.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- Source files:
  - `OpenRAModSDK/mod.config`
  - `OpenRAModSDK/launch-game.sh`
  - `OpenRAModSDK/launch-game.cmd`
  - `OpenRAModSDK/fetch-engine.sh`
  - `OpenRAModSDK/Makefile`
  - `OpenRAModSDK/make.cmd`
  - `OpenRAModSDK/make.ps1`
- Upstream documentation:
  - OpenRA Mod SDK repository: `https://github.com/OpenRA/OpenRAModSDK`
  - OpenRA engine repository: `https://github.com/OpenRA/OpenRA`
  - OpenRA wiki / FAQ: `https://wiki.openra.net/FAQ`
- Related manual chapters:
  - [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) and [Part 3.3 — Build Pipeline and Packaging](Part_03_Chapter_03_Build_Packaging.md) cover packaging, the dedicated server, and the utility scripts in more detail.
  - [Part 2.1 — MiniYaml and the Rules File Format](Part_02_Chapter_01_MiniYaml.md), [Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](Part_02_Chapter_02_Manifest.md), and [Part 2.3 — FieldLoader and Type Conversions](Part_02_Chapter_03_FieldLoader.md) cover the `mod.yaml` loaded once the engine has started.

## What to read next

- [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md): review the `mod.yaml` manifest and `ModData` environment that the bootstrap scripts launch into.
- [Part 3.3 — Build Pipeline and Packaging](Part_03_Chapter_03_Build_Packaging.md): the `make` targets described here delegate to the build pipeline and packaging scripts covered there.
- [Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](Part_02_Chapter_02_Manifest.md): once the engine starts, the manifest and `ModData` classes parse the loaded configuration.