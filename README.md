PartyMode 3
-----------

Controller for addressable RGB LED strips with several useful modes.

Dependencies
============
* rpi_ws281x: https://github.com/jgarff/rpi_ws281x
* pysolar: https://pysolar.readthedocs.io/en/latest/
* hue-python-rgb-converter: https://github.com/benknight/hue-python-rgb-converter

Setup
=====

Create a PartyMode3 systemd service:
```
sudo systemctl edit --force --full partymode3.service
```

And fill it with this:
```
[Unit]
Description=PartyMode3
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=r00t
WorkingDirectory=/home/r00t/partymode3
ExecStart=/home/r00t/partymode3/startup.sh
KillMode=none

[Install]
WantedBy=multi-user.target
```

Finally, make sure it'll run at boot:
```
sudo systemctl enable partymode3.service
```

Documentation:
==============
* `sunsky.py` implemented from "A Practical Analytic Model for Daylight", Preetham et al, 1999.
  https://www.cs.duke.edu/courses/cps124/spring08/assign/07_papers/p91-preetham.pdf
