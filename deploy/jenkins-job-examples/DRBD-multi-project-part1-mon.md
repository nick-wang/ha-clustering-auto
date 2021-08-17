# Restrict where this project can be run
```
master
```

# Build periodically
```
H 23 * * * 
```

# MulitJob Phase
## Phase name
```
MonitorTrigger
```

## Phase job
### Job name
```
00-Milestone/SLE15SP3/DRBD/MonitorBuildChange-drbd-sle15sp3
```

### Kill the phase on
```
Failure
```

### Abort all other jobs
checked

### Current job parameters
#### Parameters
```
BUILD_NUMBER_FILE=${WORK_DIR}/build_no
```

### Job name
```
00-Milestone/SLE15SP3/DRBD/15SP3-DRBD
```

### Kill the phase on
```
Never
```

### Abort all other jobs
checked

### Current job parameters
#### Parameters
```
BUILD_NUMBER_FILE=${WORK_DIR}/build_no
```

-------------
jenkins version:
	jenkins-1.651.3-1.2.noarch
