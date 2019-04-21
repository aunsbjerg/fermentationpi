# Fermentation Rpi

_tbd_

## bluetooth

Set bluetooth permission inside venv

`sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python))`
