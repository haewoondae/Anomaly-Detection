# Plan: Upload osESD_R Reference Folder to Git Repository

## 1. Objectives
- Copy the reference folder `Anomaly Detection/osESD_R` into the active Git repository root (`Anomaly Detection/Python/osESD_R`).
- Exclude the internal `.git/` folder of the cloned author repository so all 92 reference files (R source code, sample datasets, documentation) are directly tracked as regular files in `haewoondae/Anomaly-Detection.git`.
- Exclude temporary/user-specific files such as `.Rproj.user` or `.Rhistory` if appropriate, while keeping all core code, datasets (`data/`), man pages (`man/`), and metadata (`DESCRIPTION`, `NAMESPACE`, `README.md`).
- Stage, commit, and push the reference folder to remote GitHub (`origin/master`).

## 2. Steps
1. Verify source folder contents in `c:\Users\ATSAdmin\OneDrive - Ackerton Technology Services\AI Agent\Anomaly Detection\osESD_R`.
2. Copy files into `c:\Users\ATSAdmin\OneDrive - Ackerton Technology Services\AI Agent\Anomaly Detection\Python\osESD_R`, omitting `.git/`.
3. Check `git status` in `Anomaly Detection/Python` to ensure proper tracking of all files (~2.8 MB).
4. Commit with descriptive message and push to `origin/master`.
5. Update documentation and progress tracking.
