---
title: Submitting and Running Jobs
---

## Overview
To submit, run, monitor, and cancel jobs on Savio, you’ll use SLURM (the Simple Linux Utility for Resource Management). SLURM is an open-source scheduler that manages jobs, job steps, nodes, partitions, and accounts on the cluster.

## Common SLURM Commands

```{list-table}
* - Command
  - Description
  - Example
* - `sbatch`
  - Submit a batch job script
  - `sbatch myjob.sh`
* - `srun`
  - Run an interactive job
  - `srun --pty bash`
* - `scancel`
  - Cancel a job
  - `scancel 12345`
* - `squeue`
  - View job queue
  - `squeue -u $USER`
* - `sq`
  - Explain why a job is pending
  - `module load sq; sq`
* - `sacctmgr`
  - Check project/account access
  - `sacctmgr -p show associations user=$USER`
* - `sinfo`
  - Show node and partition status
  - `sinfo`
* - `sacct`
  - View accounting and completed jobs
  - `sacct -j 123451`
```

## Submitting Jobs

Jobs on Savio can be batch (non-interactive) or interactive. When submitting, you must specify:
**Account (required):**
`(--account)`

Each job runs under an account that determines which resources you can use and how usage is billed.
Check your available accounts using:
```bash
sacctmgr -p show associations user=$USER
```
**Partition (required):**
`(--partition)`

Specifies the group of nodes (e.g., CPU, GPU, HTC). For example:
```bash
#SBATCH --partition=savio3_htc
```
**Time limit (required):**
`(--time)`

Specifies the maximum wall-clock time your job can run. Format: `days-hours:minutes:seconds`. For example:
```bash
#SBATCH --time=00:30:00   # 30 minutes
```
**QoS (optional; depends on your project):**
Defines job priority and limits. Common QoS values include:
- `savio_normal` — default
- `savio_debug` — for short tests
- `savio_lowprio` — low-priority preemptible jobs
For example:
```batch
#SBATCH --qos=savio_debug
```

## Example: Basic Batch Job
```bash
#!/bin/bash
#SBATCH --job-name=test
#SBATCH --account=fc_NAME
#SBATCH --partition=savio3_htc
#SBATCH --time=00:00:30

echo "Hello world from Savio!"
```
Submit with:
```bash
sbatch myjob.sh
```
Output is saved as:
```bash
slurm-<jobid>.out
```

## Interactive Jobs
For interactive sessions (e.g., debugging, testing, GUI tools):
```bash
srun --pty -A <account> -p <partition> -t 00:30:00 bash -i
```

You’ll see:
```bash
srun: job 669120 queued and waiting for resources
srun: job 669120 has been allocated resources
[user@n0047 ~]$
```
Now you’re on a compute node. Run your commands normally.

## Job Arrays
Use job arrays to run multiple similar jobs efficiently:
```bash
#!/bin/bash
#SBATCH --job-name=array_example
#SBATCH --account=fc_NAME
#SBATCH --partition=savio3_htc
#SBATCH --array=0-31
#SBATCH --output=array_job_%A_task_%a.out
#SBATCH --error=array_job_%A_task_%a.err
#SBATCH --time=00:01:00

echo "Running task $SLURM_ARRAY_TASK_ID"
```

Submit with:
```bash
sbatch array_job.sh
```
Each array element runs as a separate job (`task 0`, `task 1`, etc.).

## Low Priority Jobs
Use the `savio_lowprio` QoS to take advantage of idle cluster resources.
- Pros: Doesn’t count toward your condo allocation
- Cons: Lower priority and can be preempted (killed or requeued)

**Example:**
```bash
#SBATCH --qos=savio_lowprio
#SBATCH --requeue
```

## Email Notifications and Output Files
By default, SLURM writes all job output to `slurm-%j.out`. To customize this:
```bash
#SBATCH --output=myjob_%j.out
#SBATCH --error=myjob_%j.err
```

If you would like to receive email updates:
```bash
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=EMAIL
```

**Example:**
```bash
#!/bin/bash
#SBATCH --job-name=test
#SBATCH --account=fc_NAME
#SBATCH --partition=savio3_htc
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:00:30
#SBATCH --output=test_%j.out
#SBATCH --error=test_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=EMAIL

echo "hello world"
```

## Monitoring Jobs
**Via Command Line**

```{list-table}
* - Command
  - Purpose
  - Example
* - `squeue -u $USER`
  - View active jobs
  - 
* - `sacct -j <jobid>`
  - View completed job info
  - `sacct -j 12345 --format=JobID,JobName,Elapsed,MaxRSS`
* - `sinfo`
  - Show node/partition status
  - `sinfo -p savio3_htc`
* - `wwall -j <jobid>`
  - Check resource usage snapshot
  - 
* - `wwtop`
  - “top”-like node summary
  - 
```
To monitor a running job interactively:
```bash
srun --jobid=<jobid> --pty /bin/bash
```

**Via MyBRC Portal**
1. Visit [MyBRC Portal](https://mybrc.brc.berkeley.edu/) and go to `Jobs → Job List`
2. Filter by user/project
3. Click a job’s SLURM ID to view:
- Start/end times
- Nodes used
- CPUs & memory
- Service Units consumed


## Pending Jobs
To diagnose pending jobs:
```bash
module load sq
sq
```
will provide you with an explanation.

For a raw queue check:
```bash
squeue -p <partition_name> --state=PD -l
```

To estimate start time:
```bash
squeue -j <jobid> --start
```

Tips to start faster:
- Request fewer nodes or shorter wall time
- Submit to a less-busy partition
- Use `sinfo` to see idle nodes
- Use `savio_lowprio` QoS when possible

For more details on using running and submitting jobs, look at the [full documentation](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/running-your-jobs/) provided by Research IT.