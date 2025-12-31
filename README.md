Here’s a clean, professional **README.md** you can drop directly into your project root.

---

# KivyMD Application – WSL Environment & Android Build Setup

This document describes the environment fixes, dependency resolutions, and build steps required to successfully run and build this KivyMD application inside **WSL** and package it for **Android**.

---

## Overview

Several system-level and Python dependency issues were preventing the application from running correctly and from building for Android. These have now been fully resolved.

The environment is verified for:

* Local execution inside WSL
* Android builds using **Buildozer**
* Latest recommended **KivyMD (2.0.1.dev0)**

---

## Changes Made

### 1. System Libraries (WSL)

The following missing system libraries were installed to ensure proper runtime and build support:

* **libmtdev1** – Required for multi-touch input support
* **xclip**, **xsel** – Clipboard integration for Kivy/KivyMD
* **pkg-config**, **libcairo2-dev**, **libgirepository1.0-dev** – Required to compile `pycairo`
* **autoconf**, **automake**, **libtool** – Required for building native dependencies (e.g., `libffi`) during Android builds

---

### 2. Python Dependencies

* **KivyMD upgraded to `2.0.1.dev0`** (installed from the master branch)
* Resolved `pycairo` build failures by installing missing system headers
* Updated core build tools:

  * `pip`
  * `setuptools`
  * `wheel`
  * `Cython`

---

## Verification Results

### Installed System Libraries

The following packages are confirmed as installed in WSL:

```text
ii  libmtdev1:amd64   1.1.6-1build4   amd64   Multitouch Protocol Translation Library
ii  xclip             0.13-2          amd64   Command line interface to X selections
ii  xsel              1.2.0-3build1   amd64   Command-line tool to manipulate X selections
```

---

### KivyMD Version

```text
Name: KivyMD
Version: 2.0.1.dev0
Summary: Material Design widgets for the Kivy framework
```

---

## Android Build Environment

The environment is fully prepared for Android builds:

* Installed **OpenJDK 17**
* Installed **build-essential**, **cmake**, **ninja-build**
* Installed all required Python and system headers for cross-compiling
* Ensured modern build tooling inside the virtual environment

---

## Quick Reference – Build & Run Commands

### 1. Install System Dependencies (WSL)

Run once on a fresh WSL installation:

```bash
sudo apt-get update && sudo apt-get install -y \
    build-essential git zip unzip openjdk-17-jdk \
    autoconf automake libtool pkg-config cmake ninja-build \
    zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev \
    libssl-dev libreadline-dev libffi-dev libsqlite3-dev \
    libbz2-dev libxslt1-dev libxml2-dev python3-dev \
    ccache libltdl-dev libmtdev1 xclip xsel
```

---

### 2. Environment Setup

Activate your virtual environment and install Python dependencies:

```bash
source ~/buildozer-env/bin/activate
pip install --upgrade pip setuptools wheel Cython
pip install https://github.com/kivymd/KivyMD/archive/master.zip
```

---

### 3. Run the App Locally

```bash
source ~/buildozer-env/bin/activate
python main.py
```

---

### 4. Build for Android

```bash
source ~/buildozer-env/bin/activate
buildozer android clean
buildozer android debug
```

---

## Notes

* First-time Android builds can take **significant time** due to NDK, SDK, and Python cross-compilation.
* Subsequent builds will be much faster.
* This setup is compatible with the **latest Kivy** and **recommended KivyMD development branch**.

---
