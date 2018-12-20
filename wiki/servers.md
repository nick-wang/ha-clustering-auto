### bj-ha-6
10.67.160.106
10.67.161.106
root
suse

### HA-5
10.67.160.105
10.67.161.105
root
suse

### HA-4
10.67.160.104
10.67.161.104
root
suse

### HA-3
10.67.160.103
10.67.161.103
root
novell

### HA-2
10.67.160.102
10.67.161.102
root
suse

### HA-1
10.67.160.101
10.67.161.101
root
novell

### C610
10.67.160.107
10.67.161.107
ask Malin for help...


### HA200 (Intel blue machine)
10.67.160.200
10.67.161.200
ask Malin for help...

jenkins server deployed on this machine


### HA dhcp and dns server (VM deployed by infra@ team)
10.67.160.10
root
suse

use yast to configure dhcp/dns

All ip range for HA team is from 
10.67.160.0/21 (8*254)

for our servers ip range, dhcp fixed:
10.67.160.0/24 and 10.67.161.0/24

other host like virtual machines use dhcp for an ip address
these addresses start from 10.67.162.0, but I do not know the
upper limit
So far, only 160.0/24 is assigned via dhcp. May possible to
extend via modify range in dhpd.conf


### racktable
https://racktables.nue.suse.com
(Using mail box uname/passwd)
http://racktable.suse.de/
This site is totally different from what it was

So useless based on the comment...


### Admin
infra@suse.de
or
Martin Caj mcaj@suse.de


### Others
Now "L" port on R&D can enter the same subnet of server room.
Send mail to infra@ if necessary
