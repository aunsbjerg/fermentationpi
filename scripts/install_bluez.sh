#!/bin/bash

set -o errexit

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# install dependencies, normal + ble
apt-get update
apt-get install -y \
    libusb-dev \
    libdbus-1-dev \
    libglib2.0-dev \
    libudev-dev \
    libical-dev \
    libreadline-dev \
    libbluetooth-dev

# constants
BLUEZ=bluez-5.50
TARBALL="$BLUEZ.tar.xz"

# download and extract
pushd /tmp
wget "http://www.kernel.org/pub/linux/bluetooth/$TARBALL"
tar xvf "$TARBALL"

# install
cd "$BLUEZ"
./configure
make
make install

# enable bluetooth service
systemctl enable bluetooth
echo "Bluez installed and service enabled - restart system needed"
