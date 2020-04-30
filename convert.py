import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("session")
args = parser.parse_args()
sess = args.session

root = os.getcwd() 
import subprocess
count = 0
media = "/media/" + sess
for dir in sorted(os.listdir(root+media)):
    ext = dir.split(".")[-1]
    if ext == 'webm':
        count += 1
        # subprocess.call("ls", cwd=root+media)
        subprocess.call("ffmpeg -i {} {}".format(dir, "video-"+str(count)+".avi"), cwd=root+media) 
        # os.remove(root+"/"+dir)
