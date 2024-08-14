# py-jq-utils
Some extra utilities built in python, to make jq more useful



## Requirement
Install jq
```
sudo apt install jq
```

Install 7z
```
sudo apt install p7zip-full
```

jq is command line JSON parser, that can do queries, and transform into other JSON.

make the python files, into executeable shell scripts
```
chmod +x *.py
```

The .py files all have schbang at top of file, to tell bash, what interpreter to run the script.  Otherwise, you need to run them as python programs:
```
python <program>.py <arguments>
```

The "./" at beginning of each .py command, is b/c in Linux, the current directory "." is usually not defaulted to by, being in the command search $PATH variable.  So to get around that, we explcitly tell it which directory the command is in.


## test data
extract test data to try samples
```
7z
```



## distfrom.py
Make complex calculated field, too complicated to use a JSON transform for:
```
jq -c . gpspipe_json/*.json  |./distfrom.py 49.199170 -122.979457
```
the distfrom.py, uses the haversine equation, which is complicated.  and expects a .lat and .lon in each JSON object.  and outputs a .distance field in meters, representing the distance from the record, from the input.  The haversine equation is rather complicated, so I implemented it different file, but you do complex calculations in same way.

You can make a simple JSON transform in jq, without using a external program, to transform JSON from one form, to another.  Below, we remove other fields, and add a 2x easy computed field delta_lat, delta_lon:
```
jq {timestamp:, lat:.lat, lon:.lon, delta_lat:(.lat-49.199170), delta:(.lon-(-122.979457))} gpspipe_json/*.json 
```
adds a distance in meters field, to every JSON object, recording distance from house.


## histfrom.py
Make a histogram from many JSON

This is a sample of how to make aggregating function, to suplement jq
```
./histfrom.py  [bin name] [value] [bin name] [... [value] [bin name]] [valuekey] [optional:filename]
```

Example:
```
cat victron_json/victron2407??_2350* | ./histfrom.py  0to200W 200 200to400W 400 400to600W 600 600to800W 800 800to1000W 1000 1000to1200W 1200 1200to1400W 1400 1400to1600W 1600 1600to1800W 1800 1800Wplus  .payload.yield_today
```
creates bins: 0to200W 200to400W 400to600W 600to800W 800to1000W 1000to1200W 1400to1600W 1600to1800W 1800Wplus
and counts of values straddled between left and right of the argument

This is if you find creating a group by in jq, too complicated:
```
./jqoin.py 'renogy_json/' filename:6:19 'victron_json/' filename:7:20  \
| jq '.|select(.b.json.payload.charge_state=="bulk" or .b.json.payload.charge_state=="off")'  \
| jq -s '.|group_by(.a.json.now[5:7],.a.json.now[11:13]) | map([first.a.json.now,first.a.json.now[5:7],first.a.json.now[11:13],(map(.b.json.payload.battery_charging_current)| add/length),(map(.b.json.payload.yield_today)| add/length)]) | group_by(.[1]) | map({"mm":first[1],data:(.|sort_by(.[2])|map(.[3])),complete:(.|sort_by(.[2])|map(.[2])),"wh":(.|map(.[4])|max),"ah":(.|map(.[3])|add) })'  
```
This produces a JSON that shows the average of solar amps on a particular hour of the day, for every month.  .a.json.now[5:7],.a.json.now[11:13] represents the month, and hour, in the .now field.


## jqoin.py
"Inner Join" 2 different streams of JSON.  Correlating 2 different JSON, to single relationship

You can supply just a directory as source of JSON, and parts of filename to correlate the object.  Theoretically this is fastest, but in practice I've seen no difference.  Probably bc the correlation algorithm I use, is probably unsophisticated and takes a long time, compared to the huge difference betwwen that is supposed to exist between reading filenames, and the contents of all the files.
```
./jqoin.py "renogy_json/renogy*" filename:6:19 "victron_json/victron*" filename:7:20
```
This will create a record for each file whose filenames match on char 6-19 and char 7-20, from each directory respectively.  This record will have .a field representing the first directory object, .b representing the 2nd directory object, and .key representing the part of the filename that matches for both files

You can use fields inside JSON, to do correlation between fields inside the JSON
```
./jqoin.py "renogy_json/renogy*" .now:0:17 "victron_json/victron*" .now:0:17
```
This will create a record for each file whose .now field's first 17 characters (so it excludes the seconds value), with a, b, and the key which contains the matching part of the value in both directory's object's .now fields.


One of the JSON streams can be supplied by pipe redirection to stdin (but no filename match this way):
```
cat gpspipe_json/* | ./jqoin.py "iperf_json/" .now:0:17 --key .now:0:17 
```
This will create a record for each object in gpspipe_json streamed in stdin, whose .now field's first 17 characters (so it excludes the seconds value), with a, b, and the key which contains the matching part of the value in iperf_json directory's object's .now fields.




## testdata
gpspipe_json has gpsdata, multiple JSON objects per file
iperf_json has gpsdata, 1 JSON object per file
renogy_json has gpsdata, 1 JSON object per file
victron_json has gpsdata, only the first JSON in file is relevant

jqjoin.py will accept multiple objects from stdin
BUT only accepts first JSON object per file.





