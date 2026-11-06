# How to publish a new version of LUCI

LUCI has **one public repository**: `https://github.com/cruzolijavier/LUCI`. It holds all the code and, under
**Releases**, the executables built by GitHub Actions.

## Publish a version (always the same)

From the LUCI folder, in PowerShell:

```powershell
.\publish.ps1 -Version 0.3.1 -Notes "- What changed`n- Something else"
```

The script updates the version number, commits everything, creates the tag `v0.3.1` and pushes it.
GitHub builds (10-15 minutes, **Actions** tab) and creates a release with two files:

- `LUCI_windows.zip`: the `LUCI` folder (LUCI.exe + luci-cli.exe + `_internal`).
- `version.json`: version, SHA-256 and size of the zip. The **Update LUCI** button reads it.

## What users who already have LUCI see

- On start (and every hour) LUCI reads `version.json`. If there is a newer version, a notice appears once and
  the **Update LUCI** button (top right) shows a red **!**.
- **Update now** downloads the zip, checks the SHA-256, closes LUCI, replaces the files in its folder and opens
  it again. Nothing is moved or renamed, so shortcuts keep working.
- Environments, settings and the OpenAI key live in `%LOCALAPPDATA%\LUCI`, outside the program folder, and
  are never touched.
- It does not update while a workflow is running, or if the LUCI folder is not writable (for example
  `C:\Program Files`).

## The OpenAI key and the robot

The executables built by GitHub contain **no key** (the repository is public: anyone could extract it from
the .exe). The assistant's robot is **grey** until someone pastes a key in **Tools > Settings > OpenAI API
key**; then it turns on by itself. `packaging/build_exe.bat` (local build) can still pack a key for internal
use, but that .exe must not be uploaded to GitHub.

## First time

1. Create the empty public repository `LUCI` on GitHub (no README, no .gitignore).
2. In the LUCI folder:

   ```powershell
   git init -b main
   git add -A
   git status        # check that openai_key.txt and bundled_key.txt do NOT appear
   git commit -m "LUCI: initial code"
   git remote add origin https://github.com/cruzolijavier/LUCI.git
   git push -u origin main
   ```

3. On GitHub: **Settings > Actions > General > Workflow permissions** = *Read and write permissions*.
4. Publish the first version (`.\publish.ps1 -Version 0.3.0 -Notes "First version with updates"`),
   download `LUCI_windows.zip` from Releases, unzip it and share that folder.
5. To test the cycle, publish `0.3.1` and press **Update LUCI** in 0.3.0.

## If something fails

- Update log: `%LOCALAPPDATA%\LUCI\update.log`.
- If the build fails, see the **Actions** tab; nothing is published until it succeeds.
- To withdraw a bad version, delete its release (and tag) on GitHub; the previous one becomes "latest" again.
