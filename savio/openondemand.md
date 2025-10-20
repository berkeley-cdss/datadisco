---
title: Open OnDemand
---

## Overview
Open OnDemand (OOD) provides browser-based, interactive access to Savio at https://ood.brc.berkeley.edu. You can launch desktops and apps, browse files, submit/monitor Slurm jobs, and open a terminal—all from your browser.

Some apps and services that are provided are:
- OOD Desktop
- Jupyter notebooks
- RStudio
- MATLAB via a Desktop environment
- VS Code
- File browsing
- Slurm job listing
- Terminal/shell access

## Logging In
1. Visit https://ood.brc.berkeley.edu.
2. Authenticate via CILogon (choose University of California, Berkeley unless otherwise directed) and login with your UC Berkeley credentials.

## Service Unit Charges
Most OOD apps launch Slurm interactive sessions behind the scenes. They incur SUs just like regular Slurm jobs.

Two shared `nodes—n0000.savio4` and `n0001.savio4` (partition: `ood-inter`) are provided for low-intensity work and do not consume SUs. Treat these like login nodes (no heavy computation). Time is charged from the moment a node is allocated until you stop the session, even if the browser tab is closed.

To check usage, go to `My Interactive Sessions` and view all currently running jobs under `Jobs → Active Jobs`. 

## Using Open OnDemand
**Files App**

Navigate to `Files → Home Directory` to:
- View, create, rename, and delete files/folders
- Upload/download files (For large transfers, use Globus instead)

**View Active Jobs**

`Jobs → Active Jobs` lets you view/cancel Slurm jobs, including those created by sbatch/srun and sessions launched via OOD.

**Shell Access**

Open a cluster shell via Clusters → BRC Shell Access.

**Interactive Apps**

Launch from Interactive Apps (top menu). Available options include:
- Desktop App (full GUI desktop on Savio)
- Jupyter Server
- RStudio Server
- Code Server (VS Code)

**Desktop App**

Use the Desktop App for GUI software (e.g., MATLAB GUI), light visualization, and file management.

To start a desktop session:
1. Log in at https://ood.brc.berkeley.edu.
2. Go to `Interactive Apps → Desktop` and choose shared node (exploration/debugging; no SUs) or compute via Slurm (SUs apply).
3. Fill the form → Launch.
4. Adjust image quality/compression if needed → Launch Desktop, which will open a new tab with your desktop session.
5. To open a command line terminal, use the file manager in the desktop or right-click the desktop → Open Terminal Here

**Jupyter Server**

Choose Jupyter Server under Interactive Apps. You will have the option to run on shared nodes (no SUs; low intensity) or via Slurm partitions (SUs apply). When finished, go to `My Interactive Sessions` and `Delete` the session to stop charges

Don’t submit Slurm jobs from the terminal inside Jupyter. The Jupyter server itself is running inside a Slurm job; launching jobs from within it (job-in-job) can cause failures. For job submission from a browser, use Clusters → BRC Shell Access instead.

**RStudio Server**

Launch via `Interactive Apps → RStudio Server`. There are three available modes:
- Compute via Slurm (SUs apply; choose resources)
- Compute on shared OOD node (no SUs; ≤ 8 GB RAM; a few cores only)
- Stop charges by Deleting the session under `My Interactive Sessions`

For packages needing compilation or external libs, install from a command-line R session (outside OOD RStudio). Once installed, they’ll be available in RStudio.

Some variables (e.g., SLURM_CPUS_ON_NODE) are not visible inside OOD RStudio via `Sys.getenv()` or `system()`.

**Code Server (VS Code)**

Launch Code Server (VS Code in the browser). There are two available modes: 
- Compute via Slurm (SUs apply)
- Exploration/debugging on shared nodes (no SUs; ≤ 8 GB RAM; a few cores)

VS Code Remote SSH is not allowed for Savio for security reasons. Use Code Server via OOD instead.

For more details on using Open OnDemand, look at the [full documentation](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/ood/#code-server-vs-code) provided by Research IT.
