#!/usr/bin/env python3

import sys
import os
from os import isatty
from datetime import datetime
#from itertools import chain
import string

# Python program to read
# json file
 
import json
import math

def calc_distance(gpx,tpv):
    PI = math.pi  #3.14159265359
    # gpx = this.gpx;
    if(gpx==None):
        return -1
    lat1 = tpv["lat"]
    lon1 = tpv["lon"]
    lat2 = gpx["lat"]
    lon2 = gpx["lon"]
    # https://www.movable-type.co.uk/scripts/latlong.html#:~:text=%E2%88%9Ax%C2%B2%20%2B%20y%C2%B2-,JavaScript%3A,trigs%20%2B%202%20sqrts%20for%20haversine.
    R = 6371000  # 6371e3; // metres
    φ1 = lat1 * PI/180.0  # φ, λ in radians
    φ2 = lat2 * PI/180.0
    Δφ = (lat2-lat1) * PI/180.0
    Δλ = (lon2-lon1) * PI/180.0

    a = math.sin(Δφ/2) * math.sin(Δφ/2) + \
        math.cos(φ1) * math.cos(φ2) * \
        math.sin(Δλ/2) * math.sin(Δλ/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    d = R * c; #// in metres
    #Note in these scripts, I generally use lat/lon for lati­tude/longi­tude in degrees,
    # and φ/λ for lati­tude/longi­tude in radians – having found that mixing degrees & radians 
    # is often the easiest route to head-scratching bugs...*/
    return d;




def get_stdin():
    # buffer = bytearray()
    # if the json file gets big, you might want to read in 4k chunks
    # and stop when it hits a closing token

    # READS from stdin
    # this version, loeds entire small JSON file into memory
    i = 0
    start = -1
    end = -1
    incre = None
    decre = None
    count = 0
    buffer = []
    stdin1 = sys.stdin.read(1)
    while len(stdin1)!=0:
      ch = stdin1[0]
      buffer.append(ch)
      if count!=0:
        if ch==incre:
          count+=1
        elif ch==decre:
          count-=1
          if count<=0:
            end = i
            # returns JSON object as 
            # a dictionary
            data = json.loads( "".join(buffer[start:end+1]) )
            yield data
            # break
            buffer = []
            start = -1
            end = -1
            i = -1
            decre=None
            incre=None
      elif start==-1 and (ch=='{' or ch=='[') :
        start = i
        count = 1
        if ch=='{':
          incre='{'
          decre='}'
        elif ch=='[':
          incre='['
          decre=']'
      elif start==-1 and (ch=='\n' or ch=='\r' or ch=='\t' or ch==' ') :
        pass # skip whitespace
      else:
          raise Exception("Runtime error.  More than 1 start condition for JSON detected")
      i+=1
      stdin1 = sys.stdin.read(1)

    if count!=0:
      sys.stderr.write(buffer)
      sys.stderr.write("\n")
      raise Exception("Runtime error.  This might not be a json")



def add(d,key,value):
    d[key] = value
    return d





if len(sys.argv) < 2:
  print("Usage: distfrom.py [lat] [lon] ")
  exit(1)

L = len(sys.argv)
lat = float(sys.argv[1])
lon = float(sys.argv[2])
gpx = {"lat":lat, "lon":lon}



# this branch loads the files into memory, processes joins
is_pipe = not isatty(sys.stdin.fileno())
if is_pipe:
    #value = map(lambda s: {"origin":{"lat":lat,"lon":lon}, "lat":s["lat"], "lon":s["lon"], "dist":calc_distance(gpx,s)}, get_stdin())
    value = map(lambda s: add(add(s,"_origin",{"lat":lat,"lon":lon}), "dist",calc_distance(gpx,s)), get_stdin())

    try:
        for item in value:
            print( json.dumps(item) )
            sys.stdout.flush() 
    except KeyboardInterrupt:
        pass

    exit(0)
else:
    sys.stderr.write("no data\n")
    exit(1)

