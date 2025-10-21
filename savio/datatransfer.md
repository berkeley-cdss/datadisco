---
title: Data Transfer
---

## Overview
When transferring data, always connect to: 
```bash
dtn.brc.berkeley.edu
```
This is Savio’s Data Transfer Node (DTN), which is designed for file movement, not computation. Executables cannot be run on the DTN, so place scripts or executables in your home or group directory instead.

There are three main transfer methods you can choose from: 
1. Globus: for large/many files
2. SFTP or SCP: small-sized data transfers
3. rclone or Git: cloud or versioned data

## Using Globus
Globus is the easiest and most robust option for medium-to-large data transfers. 
1. Visit the [Globus website](https://www.globus.org/) and either [create a free Globus ID](https://www.globusid.org/create) or login using your UC Berkeley credentials.
2. In the File Manager, turn on two-panel mode by toggling the switch near the top right.
3. In the Collection field at left, search for the Savio endpoint:
```bash
ucb#brc
```
4. Authenticate with your BRC cluster username and token PIN + one-time password (Google Authenticator).
5. In the other panel, select your personal computer or another storage endpoint.
6. Drag-and-drop files between panels and click Start.

Globus supports scheduled workflows via Globus Timer and command-line scripting using the Globus CLI. You can automate recurring backups or syncs between Savio and external endpoints. For more details on using Globus, check out the [full documentation](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/data/transferring-data/using-globus-connect-savio/).

## Using SFTP via FileZilla
This option is good for smaller file transfers.

1. If you don't already have FileZilla, download it from the [FileZilla website](https://filezilla-project.org/). Open FileZilla.
2. Open File > Site Manager > New Site and set:
- Host: `dtn.brc.berkeley.edu`
- Protocol: `SFTP - SSH File Transfer Protocol`
- Logon Type: `Interactive`
- User: `<your Savio username>`
3. Click Connect.
4. When prompted:
- Generate a one-time password using Google Authenticator.
- Enter your PIN + one-time password together.
- Uncheck “Remember password until FileZilla is closed.”
5. You’ll now see your Savio home directory.
- Drag files from local → remote to upload.
- Drag remote → local to download.

For more details on using SFTP via FileZilla, check out the [full documentation](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/data/transferring-data/using-sftp-savio-filezilla/).

## Using SCP (Command Line)
For quick terminal transfers on Mac OS/Linux:
```bash
# Upload a file to Savio
scp myfile.txt myusername@dtn.brc.berkeley.edu:/global/home/users/myusername

# Download a file from Savio
scp myusername@dtn.brc.berkeley.edu:~/myfile.txt ~/.

# Upload a folder recursively
scp -r myfolder myusername@dtn.brc.berkeley.edu:/global/scratch/users/myusername

# Download a folder
scp -r myusername@dtn.brc.berkeley.edu:~/myfolder ~/.
```
Remember to always connect to dtn.brc.berkeley.edu, not hpc.brc.berkeley.edu!

For more details on using SCP, check out the [full documentation](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/data/transferring-data/using-scp-savio/).

## Using rclone (for Box and Google Drive)
rclone is pre-installed on Savio and is great for syncing data to Box or bDrive. rclone works via command line or scripts, supports encryption and integrity checks, and can automate nightly backups.

1. SSH into the DTN:
```bash
ssh yourusername@dtn.brc.berkeley.edu
```
2. Run:
```bash
rclone config
```
3. Follow prompts to connect to Box or bDrive. (You’ll authorize your account in a browser.)

Here are some basic commands for using rclone:
```bash
# List connected remotes
rclone listremotes

# List directories in Box
rclone lsd Box:

# Copy from Savio to Box
rclone copy /global/home/users/yourusername/project Box:project_backup

# Copy from Box to Savio
rclone copy Box:admin /global/home/users/yourusername/admin

# Sync directories (two-way)
rclone sync /global/scratch/users/yourusername/data Box:data
```

For more details on using rclone, check out the [full documentation](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/data/transferring-data/rclone-box-bdrive/)




