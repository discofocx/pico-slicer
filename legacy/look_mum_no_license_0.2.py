""" Linear Batch dirty pico encoder,
    Automatically render .mov files from Vicon Cara .pico files
    """
import sys
import os
import re
import time
import datetime
import subprocess
import logging

from PyCara import PyPico
from timecode import Timecode
import cv2
import numpy

__author__ = 'Disco Hammer'
__copyright__ = 'Copyright 2017, Dragon Unit Framestore LDN 2017'
__version__ = '0.2'
__email__ = 'gsorchin@gmail.com'
__status__ = 'alpha'

# Globals

gDEBUG = True


class DirtyPicoEncoder(object):
    """Main Application"""

    def __init__(self):

        self.file_queue = list()
        self.interface = CmdUserInterface()
        self.processing_level = None

        self.cue_in = None
        self.cue_out = None



    def boot(self):
        print(58 * '=')
        print('Framestore Capturelab Dirty Pico to Quicktime encoder v0.2')
        print('Author: Gerry "Disco-Hammer" Corona')
        print(58 * '=')
        time.sleep(1)

    def scan_for_pico_files(self, ldir):
        print('\nScanning your directory for .pico files...')
        time.sleep(1)

        for path, subdirs, files in os.walk(ldir):
            for name in files:
                if name.endswith('.pico') and not os.path.isfile(path + '\\' + name.replace('.pico', '.mov')):
                    lfile = os.path.join(path, name)
                    self.file_queue.append(lfile)
                    print lfile

        if not len(self.file_queue):
            print('\nZero pico files could be found, try a different directory, bye.')
            return False
        else:
            op = self.interface.ask_for_int('\n{0} Pico file(s) have been found for encoding, do you want to proceed?\n' \
                  'Yes (1), No (0)'.format(len(self.file_queue)))
            if not op:
                return False
            else:
                return True

    def set_processing_mode(self):
        self.processing_level = self.interface.ask_for_int('Set processing level\n'
                                                           'Full files (1) or by timecode selects (0)')

    def set_process_values(self):
        if self.processing_level:
            print('Starting "full file" processing')
        else:
            print('Starting "by timecode selects" processing')
            self.cue_in, self.cue_out = self.interface.ask_for_timecode()
            print self.cue_in, self.cue_out


class CmdUserInterface(object):
    """Main interface to interact with the user from the command prompt"""
    def __init__(self):
        pass

    def ask_for_string(self, question):
        print(question)
        while True:
            answer = str(raw_input())
            if answer == '':
                print('This value can not be empty')
            else:
                break
        return answer

    def ask_for_int(self, question):
        # type: (object) -> int
        print(question)
        while True:
            try:
                answer = int(raw_input())
                if answer > 1:
                    print('Value should not be larger than 1')
                else:
                    break
            except ValueError:
                print('Numbers only, please')
        return answer

    def ask_for_timecode(self):
        gPATTERN = re.compile('^(?:(?:[0-1][0-9]|[0-2][0-3]):)(?:[0-5][0-9]:){2}(?:[0-2][0-9])$')
        print('Please supply a timecode start (##:##:##:##)')
        while True:
            tc_in = raw_input()
            if not gPATTERN.match(tc_in):
                print('That is not a valid timecode format')
            else:
                print('Please supply a timecode end (##:##:##:##)')
                tc_out = raw_input()
                if not gPATTERN.match(tc_out):
                    print('That is not a valid timecode format')
                #elif:
                #    pass
                else:
                    break
        return tc_in, tc_out

if __name__ == '__main__':
    # Initialize Application
    app = DirtyPicoEncoder()
    app.boot()

    # Set root folder for file search
    if gDEBUG:
        root = 'E:\\capturelab\\jb\\tc_test'
    else:
        root = os.getcwd()

    # Start scan for .pico files
    if app.scan_for_pico_files(root):
        app.set_processing_mode()
        app.set_process_values()
    else:
        print('Closing application.')