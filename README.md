# MFCRecorder

This is script automates the recording of public webcam shows from myfreecams. 


## Requirements

I have only tested this on debian(7+8) and Mac OS X (10.10.4), but it should run on other OSs

Requires python3.6 or newer. You can grab the newest python release from https://www.python.org/downloads/
and mfcauto.py (https://github.com/Damianonymous/mfcauto.py)

## installing and Cloning with the required modules:

to install the required modules, run: (For Debain/Ubuntu)
```
sudo apt-install update && sudo apt-install upgrade
sudo apt-install python3-pip && sudo apt-get install git
cd /home/yourusername
git clone https://github.com/Damianonymous/MFCRecorder
cd MFCRecorder
python3.6 -m pip install -r requirements.txt
python3.6 -m pip install --upgrade git+https://github.com/Damianonymous/mfcauto.py@master
Now edit the config.conf file and set the appropirate paths to your directories and wanted.txt file (see Setup)

```

to install required modules, run: (For Arch Linux, Antergos, Manjaro, etc.)
```
pacman -Syuu
pacman -S python-pip git
cd /home/yourusername
git clone https://github.com/Damianonymous/MFCRecorder
cd MFCRecorder
python3.6 -m pip install -r requirements.txt
python3.6 -m pip install --upgrade git+https://github.com/Damianonymous/mfcauto.py@master
Now edit the config.conf file and set the appropirate paths to your directories and wanted.txt file (see Setup)

```

to install the required modules, run: (For CentOS/Red Hat/Fedora) NOT TESTED BUT GOES LIKE:
```
yum update
yum upgrade
yum python-pip
yum install git
cd /home/yourusername
git clone https://github.com/Damianonymous/MFCRecorder
cd MFCRecorder
python3.6 -m pip install -r requirements.txt
python3.6 -m pip install --upgrade git+https://github.com/Damianonymous/mfcauto.py@master
Now edit the config.conf file and set the appropirate paths to your directories and wanted.txt file (see Setup)

```

## Setup

edit the config.conf file and set the appropirate paths to your directories and wanted.txt file.


## adding models to wanted list

Add models UID (user ID) to the "wanted.txt" file (only one model per line). This uses the UID instead of the name becaue the models can change their name at anytime, but their UID always stays the same. There is a number of ways to get the models UID, but the easiest would probably be to get it from the URL for their profile image. The profile image URL is formatted as (or similar to):
```
https://img.mfcimg.com/photos2/###/{uid}/avatar.90x90.jpg
```
"{uid}" is the models UID which is the number you will want to add to the "wanted.txt" file. the "###" is the first 3 digits of the models UID. For example, if the models UID is "123456789" the URL for their profile picture will be:
```
https://img.mfcimg.com/photos2/123/123456789/avatar.90x90.jpg
```

alternatively, you can use the add.py script to add models to the MFC list to enable or disable their recordings. If a model already exists, her values will be updated to any new values passed in the arguments. (requires python3.5 or newer)

Its usage is as follows:

add.py [model display name or uid] [options]

Add models to the MFC list to enable or disable their recordings. If a model
already exists, her values will be updated to any new values passed in the
arguments

positional arguments:
  model                 REQUIRED: models name or uid.

optional arguments:
  -h, --help            show this help message and exit
  -n CUSTOM_NAME, --custom_name CUSTOM_NAME
                        set a custom name for the model, otherwise the models
                        current display name will be used.
  -c COMMENT, --comment COMMENT
                        specify a comment or not for the user.
  -m MIN_VIEWERS, --min_viewers MIN_VIEWERS
                        set the minimum number of viewers this model must have
                        before recording starts
  -s STOP_VIEWERS, --stop_viewers STOP_VIEWERS
                        set the number of viewers in which the recording will
                        stop (should be less than minviewers
  -l LIST_MODE, --list_mode LIST_MODE
                        set the list mode for the model
  -b, --block           will add the model as blocked so she will not be
                        recorded even if auto recording conditions are met
  -p PRIORITY, --priority PRIORITY
                        set the priority value for the model
                        
Not passing options will add a model with all the default values, and the models current display name will be the default custom name if custom_name is not specified. 
```
python3 add.py AspenRae
```

## Web Interface (added Sep 4 2017)
There is also a web interface now, although very limited. It currently only displays the recording models along with some system statistics. If you click on a models avatar, it will open their chatroom on myfreecams site. If you click on their name above their image, it will load their profile. Below their avatar it indicates the condition for their recording (wanted, tags, viewers...) as well as the number of viewers in their room at the moment. In addition to this, there is an "Add Model" text box where you can add a model by typing in their username and submitting it. (Doing anything with the web interface, html, or css is completely new to me, so I plan to add more features, but it will take me some time since Im learning as I go.)

The default port is 8778, but it can be changed in the config file. So to view the web interface, open (https://127.0.0.1:8778/) in any web browser (note the https). If you want to access it from another computer on the same lan, replace the ip address with the ip address of that machine. 

![Image of web interface](https://i.imgur.com/9AlK3tm.jpg)


## Additional options

you can now set a custom "completed" directory where the videos will be moved when the stream ends. The variables which can be used in the naming are as follows:

**{path}** = the value set to "save directory"

**{model}** = the display name of the model

**{uid}** = the uid (user id) or broadcasters id as its often reffered in MFCs code which is a static number for the model

**{year}** = the current 4 digit year (ie:2017)

**{month}** = the current two digit month (ie: 01 for January)

**{day}** = the two digit day of the month

**{hour}** = the two digit hour in 24 hour format (ie: 1pm = 13)

**{minute}** = the current minute value in two digit format (ie: 1:28 = 28)

**{seconds}** = the current times seconds value in 2 digit format

**{auto}** = reason why the model was recorded if not in wanted list (see auto recording based on conditions below)

For example, if a made up model named "hannah" who has the uid 208562, and the "save_directory" in the config file == "/Users/Joe/MFC/": {path}/{uid}/{year}/{year}.{month}.{day}_{hour}.{minutes}.{seconds}_{model}.mp4 = "/Users/Joe/MFC/208562/2017/2017.07.26_19.34.47_hannah.mp4"


You can create your own "post processing" script which can be called at the end of the stream. The parameters which will be passed to the script are as follows:

1 = full file path (ie: /Users/Joe/MFC/208562/2017/2017.07.26_19.34.47_hannah.mp4)

2 = filename (ie : 2017.07.26_19.34.47_hannah.mp4)

3 = directory (ie : /Users/Joe/MFC/208562/hannah/2017/)

4 = models name (ie: hannah)

5 = uid (ie: 208562 as given in the directory/file naming structure example above)


## Conditional recording

In the config file you can specify conditions in which models who are not in the wnated list should be recorded. There is also a blacklist you can create and add models UID to if you want to specify models who will not be recorded even if these conditions are met.

**Tags**: you can add a comma (,) separated list of tags which models will be checked against each models specified tags.

**minTags**: indicates the minimum number of tags from the "Tags" option which must be met to start recording a model.

**newerThanHours**: If a model has joined the site in less than the number of hours specified here, the model will be recorded until she has been a model for longer than this time (it will continue to record any active recording started prior to this time).

**score**: any model with a camscore greater than this number will be recorded

**viewers**: when a model reachest this number of viewers in her chatroom, she will be recorded. This can be used to catch models as many users are entering the chat which usually indicates some sort of show has started.

**autoStopViewers**: This only apples to models who are being recorded based on the viewers condition above. The session will stop recording when the number of viewers drops below this number. Make sure there is enough of a difference between these two numbers (viewers and autoStopViewers) to avoid the show continuously starting and stopping as the number of viewers moves above/below these numbers.




# User Submitted Scripts

User submitted scripts can be found in the 'scripts' directory. These are not scripts which are created by me (beaston02), but other users who are sharing with the comunity.

## merge.py
Created by [sKanoodle](https://github.com/sKanoodle)

This script will encode and merge recordings from individual models.

#### SETTINGS

**sourcefolder**: directory with model ID subdirectories

**destinationfolder**: directory to save the encoded files in

**creationregex**: regex for parsing creation date and time from filename

**logfilepath**: logfile path (leave as empty string if no logging is desired)

**ffmpegcommand**: {0} is the absoulte source file path, {1} is the absolute target file path

**extension**: extension of the encoded file

**ffmpegmergecommand**: {0} is the absolute path of the file with parts to concat, {1} is the absolute target file path

**tmpconcatfilename**: name to use for the temp file. filename must not exist already directly in the sourcefolder

**concatmaxtime**: max time in minutes that is allowed between the end of a video and the beginning of the next video to concatinate them

**ignorefreshvideostime**: time in minutes that has to have passed since the last modification of a recording to include it for encoding. (should always be larger than concatmaxtime, otherwise the file will be encoded even if a next file would have been eligible to be concatinated to it)

**datetimeformat**: format of time and date in the file names



#### OPTIONS

**-d, --dryrun**: Simulates encoding of all files in the source folder. Size and duration of some videos might differ, because there is no concatination performed, although the status output expects concatinated videos. It will therefore only show size and duration of the first file that should be concatinated


**-c, --copy**: Only copies the video files instead of encoding them, but still merges them beforehand

**-r, --remove**: Deletes video when detected as faulty when trying to merge videos, otherwise the file will just be ignored



#### NOTES

only tested on linux.
Can be ran as a cron job to automatically merge and encode files. Encoding should reduce the size of the files

## symlink.py
Created by [sKanoodle](https://github.com/sKanoodle)

#### SETTINGS

**models**: a dictionary where the keys are the models UIDs, and the values are their usernames.

**encodedfilesdir**: the directory containing the recorded videos

**symlinkdir**: the directory where you want the recordings to be linked to using the models name instead of their UID as the directory name.

**wantedfile**: the path to the wanted file used by MFCRecorder.

#### NOTES

This script will create a symlink for the models UID directories to a directory using the models name. This will make it easier to browse through the recorded files by having directories named after the models instead of their UIDs, while still keeping all of their recordings in a single directory if/when the model changes her display name.

Only tested on linux

## postProcessing.py and test_postProcessing.py

Example of a post processing script to encode (or move, filter, etc.) files directly after the recording ended. test_postProcessing.py emulates the call from the main script (MFCRecorder.py), so that postProcessing.py can be tested independently. For more information refer to the comments inside the scripts.
