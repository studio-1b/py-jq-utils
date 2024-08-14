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




def to_bins(lst):
    last=None
    b=[]
    for i in range(0,lst.length,2):
      o={bin:lst[i], min:last, max:lst[i+1], count:0 }
      b.append(o)
      print(o)
    o={bin:lst[lst.length-1], min:last, max:None, count:0 }
    b.append(o)
    return b;

def count(bins,o,key):
    value = o[key]
    for b in bins:
      if b.min==None and value<b.max:
        b.count+=1
        break
      elif b.max==None and b.min<value:
        b.count+=1
        break
      elif b.min<value and value<b.max:
        b.count+=1
        break
    return value



if len(sys.argv) < 4:
  print("Usage: | histfrom.py [bin name] [value] [bin name] [... [value] [bin name]] [valuekey] [optional:filename]")
  print("   echo '{count:1}' | histfrom.py 'A' 10 'B' 20 'C' 'count'")
  print("   {bin:A, min:None, max:10, count:1}")
  print("   {bin:B, min:10,   max:20, count:0}")
  print("   {bin:C, min:10,   max:None, count:0}")
  exit(1)

bins=[]
L = len(sys.argv)
if L % 2 == 0:
  b=to_bins(sys.argv[1:L]);
else:
  b=to_bins(sys.argv[1:L-1]);



# this branch loads the files into memory, processes joins
is_pipe = not isatty(sys.stdin.fileno())
if is_pipe:
    #value = map(lambda s: {"origin":{"lat":lat,"lon":lon}, "lat":s["lat"], "lon":s["lon"], "dist":calc_distance(gpx,s)}, get_stdin())
    value = map(lambda s: count(bins,s), get_stdin())

    try:
        for item in bins:
            print( json.dumps(item) )
            sys.stdout.flush() 
    except KeyboardInterrupt:
        pass

    exit(0)
else:
    sys.stderr.write("no data\n")
    exit(1)

