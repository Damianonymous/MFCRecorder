#!/usr/bin/env python3
import subprocess

#change all strings to match your test environment. DO NOT TEST ON REAL RECORDINGS FOLDER
postProcessingCommand = "python3 /path/to/postProcessing.py"
subprocess.call(postProcessingCommand.split() + ["path/to/testVideo.mp4", "testVideo.mp4", "/path/to/", "someModel", "123456"])
