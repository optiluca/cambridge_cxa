lirc needs to be installed on host, unfortunately

Steps:

- apt install lirc
- edit /boot/config.txt, commenting out line with lirc-tx, and setting the correct GPIO pin to match where the IR led is actually connected
- edit /etc/lirc/lirc_options.conf, setting driver = default and device = /dev/lirc0
- copy CXA81.lircd.conf into /etc/lirc/lircd.conf.d/