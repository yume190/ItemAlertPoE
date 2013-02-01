#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

"""
sku wrote this program. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return.
"""

import atexit, winsound, threading
from os import system as OMGDONT
from ItemList import getItem, getItemName
from NotifyItems import getNotifyItems
from pydbg import *
from pydbg.defines import *

ALERT_VERSION = '20130202a'
POE_VERSION = '0.10.0e'

class PlaySoundWorker(threading.Thread):
    def run(self):
        winsound.PlaySound(r'C:\Windows\Media\Sonata\Windows Notify.wav', winsound.SND_FILENAME)

class ItemAlert(object):

    BP0 = 0x005B3E79
    BP1 = 0x005B3EBD
    BP2 = 0x005B3EBF

    def __init__(self):
        atexit.register(self.atExit)
        self.dbg = pydbg()
        self.dbg.attach(self.getProcessId())
        self.baseAddress = self.getBaseAddress()
        adjustment = self.baseAddress - 0x00400000
        ItemAlert.BP0 += adjustment
        ItemAlert.BP1 += adjustment
        ItemAlert.BP2 += adjustment
        self.lastPacketBufferAddress = 0
        self.lastPacketSize = 0

    def grabPacketSize(self, dbg):
        self.lastPacketSize = dbg.get_register("eax")
        return DBG_CONTINUE

    def beforeDemanglingPacket(self, dbg):
        self.lastPacketBufferAddress = dbg.get_register("eax")
        return DBG_CONTINUE

    def afterDemanglingPacket(self, dbg):
        if self.lastPacketBufferAddress != 0 and self.lastPacketSize > 1:
            packetData = dbg.read_process_memory(self.lastPacketBufferAddress, self.lastPacketSize)
            packetData = map(lambda x: ord(x), packetData)
            for i in range(self.lastPacketSize):
                if packetData[i:i+5] == [0xf0, 0x54, 0x92, 0x8a, 0x3a]:
                    if i+0x24+0x04 < self.lastPacketBufferAddress:
                        itemId = self.makeBigEndianDword(packetData[i+0x24:i+0x24+0x4])
                        itemName = getItemName(itemId)
                        if itemName in getNotifyItems():
                            try:
                                print str.format('Detected item drop: {name}', name=itemName)
                                sound = PlaySoundWorker()
                                sound.start()
                            except: pass
        return DBG_CONTINUE

    def makeBigEndianDword(self, data):
        assert len(data) >= 4
        if type(data) == str: data = list(data)
        if type(data[0]) == str: data = map(lambda x: ord(x), data)
        assert type(data) == list and type(data[0]) == int
        return data[3] | data[2] << 8 | data[1] << 16 | data[0] << 24

    def getProcessId(self):
        clients = [x[0] for x in self.dbg.enumerate_processes() if x[1].lower().count('client.exe') == 1]
        pid = None
        if not clients or len(clients) == 0: print 'No "client.exe" process found.'
        elif len(clients) > 1: print 'Found more than one "client.exe" process.'
        else: pid = clients[0]
        return pid

    def getBaseAddress(self):
        return [x[1] for x in self.dbg.enumerate_modules() if x[0].lower().count('client.exe') == 1][0]

    def run(self):
        self.dbg.bp_set(ItemAlert.BP0, handler=self.grabPacketSize)
        self.dbg.bp_set(ItemAlert.BP1, handler=self.beforeDemanglingPacket)
        self.dbg.bp_set(ItemAlert.BP2, handler=self.afterDemanglingPacket)
        try: self.dbg.debug_event_loop()
        except: pass

    def atExit(self):
        try: self.dbg.detach()
        except: pass

def checkVersion():
    import ctypes, sys
    if ctypes.sizeof(ctypes.c_voidp) != 4:
        print 'This program only works with a 32-bit Python installation!'
        print 'The preferred (tested) version is Python 2.7, 32-bit.'
        print 'You can download it from here: http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi'
        sys.exit(1)

def main():
    OMGDONT('title Path of Exile ItemAlert by sku')
    checkVersion()
    print str.format('Starting ItemAlert {0} for Path of Exile {1} by sku', ALERT_VERSION, POE_VERSION)
    alerter = ItemAlert()
    alerter.run()

if __name__ == "__main__":
    main()