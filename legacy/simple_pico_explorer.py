import os
import time

from PyCara import PyPico
from timecode import Timecode
import cv2



root = 'E:\\capturelab\\jb\\andy_s\\20150915_1040_C_HMC016_BA1004_AA_01_AndyS_0.pico'
print('---Reader---')
reader = PyPico.PicoReader()
reader.open(root)
for i in dir(reader):

    if i.startswith('__'):
        pass

    elif i.endswith('properties'):
        properties = reader.get_properties()
        for k,v in sorted(properties.items()):
            print k, '=', v

    else:
        print i, '=', reader.__getattribute__(i)
print 20 * '-'
#
print('---File Header---')
header = reader.get_header()
for i in dir(header):

    if i.startswith('__'):
        pass

    else:
        print i, '=', header.__getattribute__(i)

print 20 * '-'
print('---Frame Header---')
frame = reader.get_frame(0)
for i in dir(frame):

    if i.startswith('__'):
        pass
    elif i.startswith('jamsync'):
        tc = frame.__getattribute__(i)
        print i, '=', tc.hours, tc.minutes, tc.seconds, tc.frames, tc.sub_frame, tc.timecode_standard
    else:
        print i, '=', frame.__getattribute__(i)

print 20 * '-'