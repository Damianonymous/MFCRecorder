#!/usr/bin/env python3
#created GitHub user sKanoodle
import os, subprocess, argparse, time, re
from datetime import datetime, timedelta

#directory with model ID subdirectories
sourcefolder = "/home/user/MFC/src"
#directory to save the encoded files in
destinationfolder = "/home/user/MFC/encoded"
#creation date regex (works for default file names, if changed in config change here as well)
#is applied to the whole path, so custom folders (for example for the year) are possible here
creationregex = '(?P<year>\d{4}).(?P<month>\d{2}).(?P<day>\d{2})_(?P<hour>\d{2})\.(?P<minute>\d{2})\.(?P<second>\d{2})'
#logfile path (leave as empty string if no logging is desired)
logfilepath = "/home/user/MFC/encoding.log"
#{0} is the absoulte source file path, {1} is the absolute target file path
ffmpegcommand = "ffmpeg -loglevel quiet -i {0} -vcodec libx264 -crf 23 {1}"
#extension of the encoded file
extension = ".mp4"
#{0} is the absolute path of the file with parts to concat, {1} is the absolute target file path
ffmpegmergecommand = "ffmpeg -v error -f concat -safe 0 -i {0} -c copy {1}"
#filename must not exist already directly in the sourcefolder
tmpconcatfilename = "concat.mp4"
#max time in minutes that is allowed between the end of a video and the beginning of the next video to concatinate them
concatmaxtime = 60
#time in minutes that has to have passed since the last modification of a recording to include it for encoding
#(should always be larger than concatmaxtime, otherwise the file will be encoded even if a next file would have been eligible to be concatinated to it)
ignorefreshvideostime = 60
#datetime format for logging purposes
datetimeformat = "{:%Y-%m-%d %X}"

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dryrun", action="store_true", dest="dryrun", help="Simulates encoding of all files in the source folder. Size and duration of some videos might differ, because there is no concatination performed, although the status output expects concatinated videos. It will therefore only show size and duration of the first file that should be concatinated.")
parser.add_argument("-c", "--copy", action="store_true", dest="copy", help="Only copies the video files instead of encoding them, but still merges them beforehand.")
parser.add_argument("-r", "--remove", action="store_true", dest="remove", help="Deletes video when detected as faulty when trying to merge videos, otherwise the file will just be ignored")
args = parser.parse_args()

def log_and_print(string):
    if not args.dryrun and logfilepath:
        with open(logfilepath, "a") as file:
            file.write(string + "\n")
    print(string)

def format_seconds(totalseconds):
    totalseconds = int(totalseconds)
    totalminutes, seconds = divmod(totalseconds, 60)
    totalhours, minutes = divmod(totalminutes, 60)
    return "{0}:{1:02d}:{2:02d}".format(totalhours, minutes, seconds)

def get_video_length_seconds(path):
    if not os.path.exists(path):
        return 0
    try:
        lengthraw = subprocess.check_output("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {0}".format(path), shell=True)
        return float(lengthraw.strip())
    except:
        return 0

def get_file_encoding_infos(sourcepath):
    if args.dryrun:
        if not os.path.exists(sourcepath):
            return {"source": sourcepath, "target": "", "size": 0, "length": 0}
    
    #relies on set structure: sourcefolder/modelID/video
    directory, file = os.path.split(sourcepath)
    filename, ext = os.path.splitext(file)
    return {"source": sourcepath,
        "target": os.path.join(destinationfolder, os.path.basename(directory), filename + extension),
        "size": os.path.getsize(sourcepath) / 1024 / 1024,
        "length": get_video_length_seconds(sourcepath)}

def parse_creation_time(path):
    m = re.search(creationregex, path)
    if not m:
        print('error in creation date regex')
        return
    dict = {k:int(v) for k, v in m.groupdict().items()}
    return datetime(dict['year'], dict['month'], dict['day'], dict['hour'], dict['minute'], dict['second'])

def calculate_eta(starttime, progress):
    if progress <= 0:
        return "calculating ETA"
    if progress >= 1:
        return "done at {}".format(datetimeformat.format(datetime.now()))
    passedseconds = (datetime.now() - starttime).total_seconds()
    estimatedduration = passedseconds / progress
    return "ETA: {}".format(datetimeformat.format(starttime + timedelta(seconds=estimatedduration)))

def concat_files(files, name):
    log_and_print("{0} merging into {1}:".format(datetimeformat.format(datetime.now()), name))
    for file in files:
        log_and_print("[{:>10,.2f} MiB] [{}] {}".format(os.path.getsize(file) / 1024 / 1024, format_seconds(get_video_length_seconds(file)), file))
    mergefilepath = os.path.join(os.path.dirname(name), "tempmergefile.txt")
    tmp = os.path.join(sourcefolder, tmpconcatfilename)
    ffmpeg = ffmpegmergecommand.format(mergefilepath, tmp)
    if args.dryrun:
        print("[DRYRUN] would create mergefile {0}".format(mergefilepath))
        print("[DRYRUN] would run {0}".format(ffmpeg))
        print("[DRYRUN] would move {0} to {1}".format(tmp, name))
    else:
        #create mergefile with info about parts
        mergefile = open(mergefilepath, "w")
        for file in files:
            mergefile.write("file '{0}'\n".format(file))
        mergefile.close()
        #concat videos
        os.system(ffmpeg)
        #delete source parts
        for file in files:
            os.remove(file)
        #move concatinated video from temp location to final location
        os.rename(tmp, name)
        #remmove the mergefile
        os.remove(mergefilepath)
        

def merge_files_in_model_directory(directory):
    #the files need to be scanned into a list first, so we can look ahead to the next file
    entries = []
    for file in sorted(os.listdir(directory)):
        filepath = os.path.join(directory, file)
        if not file.endswith(".mp4"):
            continue
        #detects empty files
        length = get_video_length_seconds(filepath)
        if not length:
            if args.remove:
                log_and_print("removing empty or faulty video file: {}".format(filepath))
                os.remove(filepath)
            else:
                log_and_print("ignoring empty or faulty video file: {}".format(filepath))
            continue
        entries.append({"creation": parse_creation_time(file),
            "modification": datetime.fromtimestamp(os.path.getmtime(filepath)),
            "length": length,
            "file": filepath})

    #now we can traverse the files we found and check if the next file is directly following the previous and merge them if necessary
    filestoencode = []
    concatlist = []
    for i in range(len(entries)):
        #last run of the loop, we dont want further execution here, just adding the last file/performing the last concatination
        if i == len(entries) - 1:
            #make sure the latest file is not written to anymore
            if entries[i]["modification"] + timedelta(minutes=ignorefreshvideostime) > datetime.now():
                log_and_print("ignoring {0} and possible previous mergable files".format(entries[i]["file"]))
                #exit the loop and dont add the files in the concat list to filestoencode, so we can merge them the next time this script runs
                break
            #last file is not being merged, add it to the filestoencode list
            if len(concatlist) < 2:
                filestoencode.append(get_file_encoding_infos(entries[i]["file"]))
            #last file is being merged, merge and then add merged file to the filestoencode list
            else:
                concat_files(concatlist, concatlist[0])
                filestoencode.append(get_file_encoding_infos(concatlist[0]))
                concatlist = []
            break
        #print("{3} {0} {1} {2}".format(entries[i]["creation"], entries[i]["modification"], entries[i]["file"], i))
        m = entries[i]["modification"]
        c = entries[i + 1]["creation"]
        #current file has a following up file that needs to be merged
        if m < c and m + timedelta(minutes=concatmaxtime) > c:
            if not entries[i]["file"] in concatlist:
                concatlist.append(entries[i]["file"])
            concatlist.append(entries[i + 1]["file"])
        #there is nothig more to be merged
        else:
            #concatlist is empty, so treat the file as normal video to be encoded
            if len(concatlist) < 1:
                filestoencode.append(get_file_encoding_infos(entries[i]["file"]))
                continue
            #concat list has a single entry, should never happen, because there is nothing to concat
            elif len(concatlist) == 1:
                log_and_print("single file in concat list?????? {0}".format(concatlist[0]))
            #concat the files and then encode the resulting new video
            else:
                concat_files(concatlist, concatlist[0])
                filestoencode.append(get_file_encoding_infos(concatlist[0]))
                concatlist = []
    return filestoencode

def merge_and_encode_everything():
    print("finding files to encode ...", end="\r")

    entries = []
    #each ID in the source folder
    for id in os.listdir(sourcefolder):
        #ID-directory
        dir = os.path.join(sourcefolder, id)
        if os.path.isdir(dir):
            entries.extend(merge_files_in_model_directory(dir))

    index = 0
    #hack to prevent division by 0
    totalsize = max(sum([entry["size"] for entry in entries]), 1)
    sizedone = 0
    #hack to prevent division by 0
    totallength = max(sum([entry["length"] for entry in entries]), 1)
    lengthdone = 0
    starttime = datetime.now()
    progresstemplate = "    {0:,.2f}/{1:,.2f} MiB ({2:.2%}) [{7}] | {3}/{4} ({5:.2%}) [{8}] | [{6}]"
    
    def get_stats():
        return [sizedone,
            totalsize,
            sizedone / totalsize,
            format_seconds(lengthdone),
            format_seconds(totallength),
            lengthdone / totallength,
            format_seconds((datetime.now() - starttime).total_seconds()),
            calculate_eta(starttime, sizedone / totalsize),
            calculate_eta(starttime, lengthdone / totallength)]

    for entry in entries:
        #create encoding target folder in case it doesnt exist
        if not args.dryrun and not os.path.exists(os.path.dirname(entry["target"])):
            os.makedirs(os.path.dirname(entry["target"]))
        index += 1
        log_and_print("{5} {0}: [{1:>10,.2f} MiB] [{2}] source: {3}, target: {4}"
            .format(datetimeformat.format(datetime.now()), entry["size"], format_seconds(entry["length"]), entry["source"], entry["target"], "{0}/{1}".format(index, len(entries)).rjust(9)))
        #print with carriage return at the end, so that this line can be overwritten by the next print
        print(progresstemplate.format(*get_stats()), end="\r")
        sizedone += entry["size"]
        lengthdone += entry["length"]
        if not args.dryrun:
            if not args.copy:
                #actual call to encode the video
                os.system(ffmpegcommand.format(entry["source"], entry["target"]))
                os.remove(entry["source"])
            else:
                #only move the video file without encoding
                os.rename(entry["source"], entry["target"])

    #final progress, should always show 100%
    print(progresstemplate.format(*get_stats()))

merge_and_encode_everything()
