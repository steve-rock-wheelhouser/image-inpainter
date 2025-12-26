# Image Inpainter RPM Packaging Guide

This document details the process, prerequisites, and structure for packaging the **Image Inpainter** application as an RPM for Fedora/RHEL-based systems.

## CRITICAL: Naming Conventions (READ THIS FIRST)

**Failure to follow these rules will result in a "Generic" package in the Software Center (missing screenshots, icons, and descriptions).**

The Linux Software Center relies on a strict link between the AppStream Metadata, the Desktop File, and the Icon.

1.  **RDNN Format Required:** Use Reverse Domain Name Notation (e.g., `com.wheelhouser.image_inpainter`).
2.  **NO HYPHENS in ID:** The App ID component must use **underscores** (`_`), not hyphens. Hyphens trigger validation errors (`cid-rdns-contains-hyphen`) that break the build.
    *   **BAD:** `com.wheelhouser.image-inpainter`
    *   **GOOD:** `com.wheelhouser.image_inpainter`
3.  **Exact Filename Matching:**
    *   **Desktop File:** `com.wheelhouser.image_inpainter.desktop`
    *   **Metainfo File:** `com.wheelhouser.image_inpainter.metainfo.xml`
    *   **Icon File:** `com.wheelhouser.image_inpainter.png`
4.  **The ID Tag MUST Include Suffix:**
    Inside the `.metainfo.xml` file, the `<id>` tag must match the desktop filename **exactly**, including the `.desktop` extension.
    ```xml
    <!-- CORRECT -->
    <id>com.wheelhouser.image_inpainter.desktop</id>
    
    <!-- INCORRECT (Will break Software Center link) -->
    <id>com.wheelhouser.image_inpainter</id>
    ```
5.  **Icon Reference:**
    The `.desktop` file must refer to the icon by its full RDNN name (without extension):
    ```ini
    Icon=com.wheelhouser.image_inpainter
    ```

---

## Overview

The packaging process is automated via `build-rpm.sh`. Unlike traditional source builds, this process bundles a pre-compiled binary (generated via Nuitka) along with necessary assets, desktop integration files, and AppStream metadata into a standard RPM package.

## Prerequisites

The build script automatically attempts to install dependencies using `dnf`. You will need:

*   **OS:** Fedora, RHEL, or compatible derivative.
*   **Tools:**
    *   `rpm-build`
    *   `rpmdevtools`
    *   `desktop-file-utils`
    *   `libappstream-glib`
    *   `rpm-sign` (optional, for signing)
    *   `appstream` (provides `appstreamcli` for validation)

## Project Structure

*   **`build-rpm.sh`**: The main orchestration script.
*   **`image_inpainter.spec`**: The RPM specification file defining dependencies and installation paths.
*   **`com.wheelhouser.image_inpainter.desktop`**: System menu integration file.
*   **`com.wheelhouser.image_inpainter.metainfo.xml`**: AppStream metadata for software center visibility.
*   **`build_pyinstaller.sh`**: Script referenced to compile the Python code into a binary using PyInstaller.

## The Build Process

To build the RPM, run the script from the project root:

```bash
./build-rpm.sh
```

### Workflow Breakdown

1.  **Version Management**:
    *   Updates the `Version` in `image_inpainter.spec`.
    *   Auto-increments the `Release` number in the spec file to ensure upgrade paths work correctly.

2.  **Pre-Build Validation**:
    *   Validates the AppStream metadata (`metainfo.xml`) using `appstreamcli`.
    *   Validates the desktop entry (`.desktop`) using `desktop-file-validate`.

3.  **Binary Compilation**:
    *   Executes `./build_pyinstaller.sh` to generate the standalone executable if it doesn't exist or is stale.

4.  **RPM Generation**:
    *   Creates a clean build environment in `rpmbuild/`.
    *   Copies assets, icons, and binaries.
    *   Runs `rpmbuild -ba` to produce the final `.rpm` file.

## Troubleshooting

### Software Center shows "Generic" icon or missing screenshots
1.  Check the **CRITICAL** section above.
2.  Ensure the `<id>` in `metainfo.xml` matches the `.desktop` filename.
3.  Ensure the `Icon=` in `.desktop` matches the installed icon filename in `/usr/share/icons/hicolor/...`.
4.  Force a cache refresh:
    ```bash
    sudo appstreamcli refresh --force && killall gnome-software
    ```

### Build fails on "cid-rdns-contains-hyphen"
You are using hyphens in your App ID (e.g., `com.wheelhouser.image-inpainter`). Rename your files and ID to use underscores (`com.wheelhouser.image_inpainter`).

## Validation Tools

We have included scripts to help verify your setup before and after installation.

### 1. Verify Source Metadata (Pre-Build)
Run this Python script to check if your source files (Desktop and Metainfo) match the naming conventions required by the Software Center.

```bash
python3 scripts/verify_metadata.py
```

### 2. Verify Installed Files (Post-Install)
After installing the RPM, run this script to verify that the files were actually placed correctly on your system and that the IDs match.

```bash
./scripts/debug_install.sh
```

### 3. Manual Validation Commands
You can also run the standard Linux validation tools manually:

**Validate Desktop File:**
```bash
desktop-file-validate com.wheelhouser.image_inpainter.desktop
```

**Validate AppStream Metadata:**
```bash
appstreamcli validate com.wheelhouser.image_inpainter.metainfo.xml
```

4.  **Source Preparation**:
    *   Creates a clean build environment in `build/rpm-source`.
    *   Bundles the binary, assets, desktop file, metadata, and license into a tarball (`image-inpainter-0.3.0.tar.gz`).
    *   This tarball serves as `Source0` for the RPM build.

5.  **RPM Build**:
    *   Sets up a local `rpmbuild` directory structure (`BUILD`, `RPMS`, `SOURCES`, etc.).
    *   Runs `rpmbuild -ba` using the generated tarball and the spec file.

## RPM Specification Details (`image-inpainter.spec`)

The spec file handles the installation logic on the end-user's system.

*   **Binary Placement**: The main binary is installed to `%{_libexecdir}/image-inpainter/` (e.g., `/usr/libexec/image-inpainter/`) to keep it private and separate from user commands.
*   **Wrapper Script**: A shell script is created at `%{_bindir}/image-inpainter` (e.g., `/usr/bin/image-inpainter`) to launch the application with specific environment variables:
    *   `GTK_THEME=Adwaita:dark`: Forces dark mode for native dialogs.
    *   `GTK_USE_PORTAL=1`: Requests modern file chooser portals (better view settings retention).
    *   `QT_QPA_PLATFORMTHEME=gtk3`: Ensures Qt uses GTK3 theming for consistency.
*   **Metadata**:
    *   Installs the `.desktop` file to `%{_datadir}/applications`.
    *   Installs the `.metainfo.xml` to `%{_metainfodir}` (usually `/usr/share/metainfo`).
*   **Icons**: Installs the application icon to `/usr/share/icons/hicolor/256x256/apps/`.

## RPM Signing

The script supports automatic GPG signing of the generated packages.

### Configuration
To enable signing, you must have a GPG key configured in your `~/.rpmmacros` file:

```
%_gpg_name <Your Key ID>
```

If configured, the script will:
1.  Export your public key to a temporary file `RPM-GPG-KEY-image-inpainter`.
2.  Import it into the local RPM database (requires `sudo`).
3.  Sign both the Binary and Source RPMs using `rpm --addsign`.
4.  Verify the signature immediately after signing.

## Output

Upon success, the artifacts are copied to the `dist/` directory in the project root:

*   **Binary RPM**: `dist/image-inpainter-0.3.0-<release>.<arch>.rpm`
*   **Source RPM**: `dist/image-inpainter-0.3.0-<release>.src.rpm`

## Installation

To install the resulting package on a Fedora/RHEL system:

```bash
sudo dnf install dist/image-inpainter-0.3.0-*.rpm
```

## Troubleshooting

*   **"rpmbuild not found"**: Ensure you have installed the `rpm-build` package.
*   **AppStream Validation Failed**: Check `com.wheelhouser.image-inpainter.metainfo.xml` for syntax errors or deprecated tags (e.g., `<developer_name>` vs `<developer>`).
*   **Signing Skipped**: Ensure `rpm-sign` is installed and `~/.rpmmacros` contains your GPG key ID.