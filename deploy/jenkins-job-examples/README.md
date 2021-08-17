# Jenkins URL is editable:
> In file jenkins.model.JenkinsLocationConfiguration.xml:  
> configure <jenkinsUrl>
```
<?xml version='1.0' encoding='UTF-8'?>
<jenkins.model.JenkinsLocationConfiguration>
  <adminAddress>slehapek-noreply@suse.com</adminAddress>
  <jenkinsUrl>http://SUSEServerTest:8080/</jenkinsUrl>
</jenkins.model.JenkinsLocationConfiguration>
```

# location of email template
> In ./email-templates/
```
/var/lib/jenkins # find . -name template.jelly
./email-templates/template.jelly
```
