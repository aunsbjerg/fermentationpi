# The MIT License (MIT)
#
# Copyright (c) 2017 Atle Frenvik Sveen (atle@frenviksveen.net)
# Copyright (c) 2018 Justin Fuhrmeister-Clarke (justin@fuhrmeister-clarke.com)
# Copyright (c) 2019 Mikkel Aunsbjerg Jakobsen (mikkelaunsbjerg@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Based on https://github.com/JustinFuhrmeister-Clarke/pytilt
# Code has been clean up, unused methods removed and syntax prettified.

import logging
import struct
import bluetooth._bluetooth as bluez


logger = logging.getLogger(__name__)


LE_META_EVENT = 0x3e
LE_PUBLIC_ADDRESS = 0x00
LE_RANDOM_ADDRESS = 0x01
LE_SET_SCAN_PARAMETERS_CP_SIZE = 7
OGF_LE_CTL = 0x08
OCF_LE_SET_SCAN_PARAMETERS = 0x000B
OCF_LE_SET_SCAN_ENABLE = 0x000C
OCF_LE_CREATE_CONN = 0x000D

LE_ROLE_MASTER = 0x00
LE_ROLE_SLAVE = 0x01

# these are actually subevents of LE_META_EVENT
EVT_LE_CONN_COMPLETE = 0x01
EVT_LE_ADVERTISING_REPORT = 0x02
EVT_LE_CONN_UPDATE_COMPLETE = 0x03
EVT_LE_READ_REMOTE_USED_FEATURES_COMPLETE = 0x04

# Advertisment event types
ADV_IND = 0x00
ADV_DIRECT_IND = 0x01
ADV_SCAN_IND = 0x02
ADV_NONCONN_IND = 0x03
ADV_SCAN_RSP = 0x04


def _return_number_packet(pkt):
    integer = 0
    multiple = 256

    for c in pkt:
        integer += c * multiple
        multiple = 1

    return integer


def _return_string_packet(pkt):
    string = ''

    for c in pkt:
        string += '%02x' % c

    return string


def _hci_toggle_le_scan(sock, enable):
    cmd_pkt = struct.pack("<BB", enable, 0x00)
    bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)


def hci_enable_le_scan(sock):
    _hci_toggle_le_scan(sock, 0x01)


def hci_disable_le_scan(sock):
    _hci_toggle_le_scan(sock, 0x00)


def create_blescan_socket(dev_id=0):
    try:
        sock = bluez.hci_open_dev(dev_id)
        old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)
        hci_enable_le_scan(sock)
        logger.info(f"blescan started for device {dev_id}")
        return sock

    except:
        logger.error(f"error accessing bluetooth device {dev_id}...")
        raise


def parse_events(sock, loop_count=100):
    """
    perform a device inquiry on bluetooth device #0
    The inquiry should last 8 * 1.28 = 10.24 seconds before the inquiry is performed, bluez should flush its cache of
    previously discovered devices.
    """
    old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)
    flt = bluez.hci_filter_new()
    bluez.hci_filter_all_events(flt)
    bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
    sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt)
    beacons = []

    for i in range(0, loop_count):
        pkt = sock.recv(255)
        ptype, event, plen = struct.unpack('BBB', pkt[:3])

        if event == LE_META_EVENT:
            subevent = pkt[3]
            pkt = pkt[4:]

            if subevent == EVT_LE_CONN_COMPLETE:
                le_handle_connection_complete(pkt)

            elif subevent == EVT_LE_ADVERTISING_REPORT:
                num_reports = pkt[0]
                report_pkt_offset = 0

                for i in range(0, num_reports):
                    beacons.append({
                        'uuid': _return_string_packet(pkt[report_pkt_offset - 22: report_pkt_offset - 6]),
                        'minor': _return_number_packet(pkt[report_pkt_offset - 4: report_pkt_offset - 2]),
                        'major': _return_number_packet(pkt[report_pkt_offset - 6: report_pkt_offset - 4])
                    })

    sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, old_filter)
    return beacons
