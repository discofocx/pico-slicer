import sys
import os
import re
import time
import datetime
import subprocess
import logging

import cv2
import numpy
from PyCara import PyPico
from timecode import Timecode


class PicoFile(object):
    def __init__(self, file_path):
        """

        :type file_path: str
        """
        self.file = None
        self.file_path = file_path

        self.header = None
        self.base_timecode = None

        self.channel = None
        self.timecode = None
        self.fps = None
        self.frame_in = None
        self.frame_out = None
        self. frame_zero = None
        self.frame_offset = None
        self.frame_start = None
        self.frame_padding = None

    def _read(self):
        """
        Loads a pico file in memory
        :return:
        """
        self.file = PyPico.PicoReader().open(self.file_path)



