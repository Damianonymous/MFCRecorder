#!/usr/bin/env python
#created by sKanoodle on GitHub
import os, sys

models = {123: "name1",
    345: "name2"}

encodedfilesdir = "/home/user/MFC/encoded"
symlinkdir = "/home/user/MFC/models"
wantedfile = "/home/user/MFC/wanted.txt"

if not os.path.exists(symlinkdir):
    os.makedirs(symlinkdir)

for file in os.listdir(symlinkdir):
    if os.path.islink(os.path.join(symlinkdir, file)):
        os.remove(os.path.join(symlinkdir, file))

#create symlinks to find recordings by model name
for id, name in models.items():
    os.symlink(os.path.join(encodedfilesdir, str(id)), os.path.join(symlinkdir, name))

#create wanted file
wanted = open(wantedfile, "w")
for id in models:
    wanted.write("{0}\n".format(id))
