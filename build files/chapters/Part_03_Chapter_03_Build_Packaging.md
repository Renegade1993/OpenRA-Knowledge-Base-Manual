# Chapter 3.3 — Build Pipeline and Packaging

## Purpose

OpenRA uses .NET for the [engine](../appendices/Appendix_A_Glossary.md) and [mod](../appendices/Appendix_A_Glossary.md) assemblies, and a collection of shell scripts for packaging and deployment. This chapter explains the build process from source to distributable packages, including the Makefile, `dotnet publish`, utility commands, and platform-specific packaging.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the full build pipeline from source to self-contained release [packages](../appendices/Appendix_A_Glossary.md).
- Use the main Makefile targets for build, test, check, and version.
- Describe the role of dotnet publish and platform-specific packaging scripts.
- Validate mod [YAML](../appendices/Appendix_A_Glossary.md) using the OpenRA [Utility](../appendices/Appendix_A_Glossary.md) commands.
- Configure project files for [TargetPlatform](../appendices/Appendix_A_Glossary.md) and target framework.
- Identify platform-specific packaging requirements (Windows, Linux, macOS).

## Files

| File | Responsibility |
| :---- | :---- |
| `Makefile` | Top-level build targets: `all`, `test`, `check`, `install`, `version`. |
| `OpenRA.Game/OpenRA.Game.csproj` | Engine project file. |
| `OpenRA.Mods.Common/OpenRA.Mods.Common.csproj` | Common mod project file. |
| `OpenRA.Mods.Cnc/OpenRA.Mods.Cnc.csproj` | C&C mod project file. |
| `OpenRA.Mods.D2k/OpenRA.Mods.D2k.csproj` | D2K mod project file. |
| `OpenRA.WindowsLauncher/` | Windows launcher project. |
| `packaging/functions.sh` | Shared packaging helper functions. |
| `packaging/windows/buildpackage.sh` | Windows installer/package builder. |
| `packaging/linux/buildpackage.sh` | Linux AppImage/package builder. |
| `packaging/macos/buildpackage.sh` | macOS app bundle builder. |
| `packaging/package-all.sh` | Builds packages for all platforms. |
| `utility.sh` | Wrapper for running the OpenRA utility. |
| `launch-game.sh` | Development launch script. |
| `fetch-geoip.sh` | Downloads GeoIP database for server IP location. |
| `configure-system-libraries.sh` | Configures system native dependencies. |
| `VERSION` | Version file used by packaging scripts. |

![Architecture diagram](images/Part_03_Chapter_03_Build_Packaging-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Build overview

```
[Source] -> [dotnet build] -> [bin/ engine + mod DLLs] -> [dotnet publish --self-contained] -> [platform package]
```

The engine and mod assemblies are built with .NET. For releases, `dotnet publish` produces a self-contained package that includes the .NET runtime and native dependencies. Platform-specific scripts then bundle the binaries into installers, app bundles, or AppImages.

### Make targets

| Target | Purpose |
| :---- | :---- |
| `make` / `make all` | Builds the engine and mods in Release mode. |
| `make test` | Builds and checks official mod YAML. |
| `make tests` | Builds and runs unit tests. |
| `make check` | Builds in Debug mode and runs code-style checks. |
| `make check-scripts` | Checks Lua script syntax. |
| `make install` | Installs engine and official mods locally. |
| `make version` | Updates version in `VERSION` and `mod.yaml` files. |
| `make install-linux-shortcuts` | Installs desktop files and icons. |

### Configuration

- `CONFIGURATION` — `Release` or `Debug`.
- `TARGETPLATFORM` — `win-x64`, `linux-x64`, `linux-arm64`, `osx-x64`, `osx-arm64`.
- `DEPENDENCIES` — `bundled` (default) or `system` for native libraries.

### Platform RID

The Makefile detects the target platform using `dotnet --info` and `uname`. Cross-platform builds are possible by setting `TARGETPLATFORM` explicitly.

![Data flow  code path diagram](images/Part_03_Chapter_03_Build_Packaging-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Build

```makefile
all:
    @$(DOTNET) build -c ${CONFIGURATION} -nologo -p:TargetPlatform=$(TARGETPLATFORM)
    @./fetch-geoip.sh
```

This compiles the solution and downloads the GeoIP database.

### Test

```makefile
test: all
    @./utility.sh ts-content --check-yaml
    @./utility.sh ts --check-yaml
    @./utility.sh d2k-content --check-yaml
    @./utility.sh d2k --check-yaml
    @./utility.sh cnc-content --check-yaml
    @./utility.sh cnc --check-yaml
    @./utility.sh ra-content --check-yaml
    @./utility.sh ra --check-yaml
```

The `utility.sh` script runs the OpenRA Utility command-line tool, which loads each mod and validates its YAML.

### Code style checks

```makefile
check:
    @$(DOTNET) build -c Debug -nologo -warnaserror -p:TargetPlatform=$(TARGETPLATFORM)
    @./utility.sh all --check-explicit-interfaces
    @./utility.sh all --check-conditional-trait-interface-overrides
```

### Publish

The `packaging/functions.sh` script uses `dotnet publish`:

```bash
dotnet publish -c Release -p:TargetPlatform="${TARGETPLATFORM}" -p:CopyGenericLauncher="${COPY_GENERIC_LAUNCHER}" -p:CopyCncDll="${COPY_CNC_DLL}" -p:CopyD2kDll="${COPY_D2K_DLL}" -r "${TARGETPLATFORM}" -p:PublishDir="${DEST_PATH}" --self-contained true
```

### Data installation

After publishing, the packaging scripts copy data:

```bash
install_data() {
    ./fetch-geoip.sh
<!-- DEV-NOTE [tooling]: Khronos GLSL reference: https://www.khronos.org/opengl/wiki/OpenGL_Shading_Language — reference for the shader dialect used by the engine. -->
    cp -r "${SRC_PATH}/glsl" "${DEST_PATH}"
    cp -r "${SRC_PATH}/mods/common" "${DEST_PATH}/mods/"
    cp -r "${SRC_PATH}/mods/${MOD_ID}" "${DEST_PATH}/mods/"
    cp -r "${SRC_PATH}/mods/common-content" "${DEST_PATH}/mods/"
    cp -r "${SRC_PATH}/mods/${MOD_ID}-content" "${DEST_PATH}/mods/"
}
```

### Platform-specific launchers

- **Windows:** `OpenRA.WindowsLauncher` builds a per-mod `.exe` with the mod name, icon, and FAQ URL embedded.
- **macOS:** `packaging/macos/buildpackage.sh` creates an `.app` bundle with the launcher, binaries, and mod data.
- **Linux:** `packaging/linux/buildpackage.sh` creates an AppImage or a portable tarball.

![Configuration (yaml) diagram](images/Part_03_Chapter_03_Build_Packaging-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Mod version

The version is stored in `VERSION` and injected into `mod.yaml` during packaging:

```bash
set_engine_version "$(VERSION)" .
set_mod_version "$(VERSION)" mods/*/mod.yaml
```

### Project files

Each C# project targets the appropriate .NET version and includes `TargetPlatform` properties:

```xml
<PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <TargetPlatform Condition="'$(TargetPlatform)' == ''">win-x64</TargetPlatform>
</PropertyGroup>
```

## Interconnectivity

- **Depends on:** [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) (`mod.yaml`, manifest), [Part 2.1 — MiniYaml and the Rules File Format](Part_02_Chapter_01_MiniYaml.md) validation, [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md) packaging.
- **Used by:** [Part 10.1 — Official Mods](Part_10_Chapter_01_Official_Mods.md) are packaged this way, and [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md) covers porting and deployment workflows.

![Algorithms diagram](images/Part_03_Chapter_03_Build_Packaging-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Dependency bundling

<!-- DEV-NOTE [tooling]: OpenAL Soft: https://openal-soft.org — the open-source implementation of the spatial audio API used by OpenRA. -->
When `DEPENDENCIES=bundled`, the build includes native libraries such as SDL2, OpenAL, and FreeType in the output. When `DEPENDENCIES=system`, it links against system libraries.

### Self-contained publish

`dotnet publish --self-contained true` bundles the .NET runtime, so players do not need to install .NET separately.

### YAML validation

The utility's `--check-yaml` command loads each mod's rules, sequences, weapons, and other YAML files and reports errors. This catches syntax errors and missing references before release.

### Explicit interface checks

`--check-explicit-interfaces` verifies that traits implement interfaces explicitly where required, preventing subtle reflection issues.

### Conditional trait interface checks

`--check-conditional-trait-interface-overrides` validates that conditional trait interfaces are correctly overridden.

### Lua syntax checks

`make check-scripts` runs `luac -p` on all Lua files in maps and scripts.

![Extension points diagram](images/Part_03_Chapter_03_Build_Packaging-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new mod to the build

Create a `.csproj` for the mod assembly, add it to the solution, and reference it in `mod.yaml`. Add the mod to the packaging scripts if it should be released.

### Add a custom build target

Extend the Makefile or add a new packaging script under `packaging/`. Use `packaging/functions.sh` to share common steps.

### Add a utility command

Implement `IUtilityCommand` in a C# class and run it via `utility.sh <mod> --command-name`. Utility commands are useful for custom tooling, data conversion, or validation.

### Add custom packaging

Create a new script under `packaging/<platform>/` and call it from `package-all.sh`. The shared functions in `packaging/functions.sh` handle assembly and data installation.

![Common pitfalls  guardrails diagram](images/Part_03_Chapter_03_Build_Packaging-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Target platform mismatch:** build and publish must use the same `TargetPlatform`. Mismatches can cause native dependency errors.
- **Runtime version:** the .NET SDK version must match the target framework in the project files.
- **GeoIP fetch:** `fetch-geoip.sh` downloads an external file. Packaging may fail if the network is unavailable; include a fallback or pre-download the file.
- **Mod version injection:** `make version` updates `mod.yaml` and `VERSION`. Commit these changes before tagging a release.
- **YAML validation warnings:** `make test` treats warnings as errors by default. Set `TREAT_WARNINGS_AS_ERRORS=false` to see warnings without failing the build.
- **Self-contained size:** self-contained packages are large. Consider trimming unused assemblies if package size is a concern.
- **macOS notarization:** macOS app bundles may require code signing and notarization for distribution outside the App Store.
- **Windows launcher:** the Windows launcher embeds the mod ID and FAQ URL. Make sure these are correct for each mod.

## Summary

This chapter explains how OpenRA builds its engine and mod assemblies from source into self-contained, platform-specific release packages.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `Makefile` — top-level build targets.
- `packaging/functions.sh` — shared packaging helpers.
- `packaging/windows/buildpackage.sh` — Windows packaging.
- `packaging/linux/buildpackage.sh` — Linux packaging.
- `packaging/macos/buildpackage.sh` — macOS packaging.
- `packaging/package-all.sh` — all-platform packaging.
- `utility.sh` — utility command wrapper.
- `launch-game.sh` — development launch.
- `fetch-geoip.sh` — GeoIP download.
- `OpenRA.Game/IUtilityCommand.cs` — utility command interface.

## What to read next

- [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md): return to the mod package layout that the build pipeline packages into release installers and archives.
- [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md): continue from packaging into porting, deployment, and development workflows for new mods.
- [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md): understand how packaged releases connect to the server infrastructure.

### External resources

- [Microsoft .NET SDK](https://dotnet.microsoft.com) — required to build the OpenRA engine and mod projects.