# This build is parameterized
## 	String Parameters
###		name
```
BUILD_NUMBER_FILE
```

###		Default Value
```
${WORKSPACE}/${BUILD_NUMBER}/build_no
```

##	Prepare an environment for the run
###		Keep Jenkins Environment Variables
checked

###		Keep Jenkins Build Variables
checked

## 	Properties Content
```
LIB_DIR=/tmp/jenkins-work/ha-share/deploy/scripts
MONITOR_LIB_DIR=/tmp/jenkins-work/ha-share/jenkins-monitor
WORK_DIR=/tmp/jenkins-work/${JOB_NAME}/${BUILD_NUMBER}
BUILD_LOG_DIR=${WORKSPACE}/${BUILD_NUMBER}
```

# Restrict where this project can be run
```
master
```

# Execute shell
```
cd ${MONITOR_LIB_DIR}
./monitor-build-change-sle15sp3.sh -D ${JOB_NAME}
```

# Post-build Actions
## 	Publish Junit test result report
###		Test report XMLs
```
**/junit-*.xml
```

###		Health report amplification factor
```
1.0
```

##	Email Notification
```
nwang@suse.com
```

##	Editable Email Notification
###		Project Recipient List
```
ha-devel@suse.de
```

###		Project Reply-To List
```
$DEFAULT_REPLYTO
```

###		Content Type
```
Default content type
```

###		Default Subject
```
$DEFAULT_SUBJECT
```

###		Default Content
```
  <hr/>
  (This mail is auto delivered, please not reply！)<br/><hr/>

   ${JELLY_SCRIPT,template="template.jelly"}
```

-------------
jenkins version:
	jenkins-1.651.3-1.2.noarch
