#!/usr/bin/env python3
import os, sys

#targetDir because when used with post processing script the MFCRecorder doesnt move files
targetDir = '/path/to/targetdir/'
#command for ffmpeg {0} is source, {1} is target
ffmpegCommand = 'ffmpeg -y -v error -i {0} -bsf:a aac_adtstoasc -codec copy {1}'
#extension for target
extension = '.mp4'

#retrieving arguments that are passed from MFCRecorder
#always crosscheck with readme
fullPath = sys.argv[1]
filename = sys.argv[2]
directory = sys.argv[3]
name = sys.argv[4]
uid = sys.argv[5]

#creating full target path, do whatever you want
file, ext = os.path.splitext(filename)
targetPath = os.path.join(targetDir, uid, file + extension)

#create dir if it doesnt exist
if not os.path.exists(os.path.dirname(targetPath)):
    os.makedirs(os.path.dirname(targetPath))

#final call for encoding
os.system(ffmpegCommand.format(fullPath, targetPath))
