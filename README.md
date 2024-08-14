# py-jq-utils
Some extra utilities built in python, to make jq more useful


## Why do you need this?
jq is command line JSON parser, that can do queries, and transform into other JSON.
This will add some simple programs to augment jq's functionality.  And some are simple enough, for you to clone and change for your own purposes.


## Requirement
Install jq
```
sudo apt install jq
```

Install 7z
```
sudo apt install p7zip-full
```


Now, make the python files, into executeable shell scripts
```
chmod +x *.py
```

Explanation for above: The .py files all have schbang at top of file, to tell bash, what interpreter to run the script.  Otherwise, you need to run them as python programs:
```
python <program>.py <arguments>
```

Explanation for sample below: The "./" at beginning of each .py command, is b/c in Linux, the current directory "." is usually not defaulted to by, being in the command search $PATH variable.  So to get around that, we explcitly tell it which directory the command is in.



## Extracting Test data for sample
extract test data to try samples
```
7z x testdata.7z
```



## Program: distfrom.py
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
<pre>
...
{... "_origin": {"lat": 49.19917, "lon": -122.979457}, "dist": 4038.909158672087}
...
</pre>

## Program: histfrom.py
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
<pre>
{"bin": "0to200W", "min": null, "max": 200.0, "count": 0}
{"bin": "200to400W", "min": 200.0, "max": 400.0, "count": 6}
{"bin": "400to600W", "min": 400.0, "max": 600.0, "count": 18}
{"bin": "600to800W", "min": 600.0, "max": 800.0, "count": 6}
{"bin": "800to1000W", "min": 800.0, "max": 1000.0, "count": 12}
{"bin": "1000to1200W", "min": 1000.0, "max": 1200.0, "count": 12}
{"bin": "1200to1400W", "min": 1200.0, "max": 1400.0, "count": 48}
{"bin": "1400to1600W", "min": 1400.0, "max": 1600.0, "count": 24}
{"bin": "1600to1800W", "min": 1600.0, "max": 1800.0, "count": 42}
{"bin": "1800Wplus", "min": 1800.0, "max": null, "count": 6}
</pre>



This is if you find creating a group by in jq, too complicated:
```
./jqoin.py 'renogy_json/' filename:6:19 'victron_json/' filename:7:20  \
| jq '.|select(.b.json.payload.charge_state=="bulk" or .b.json.payload.charge_state=="off")'  \
| jq -s '.|group_by(.a.json.now[5:7],.a.json.now[11:13]) | map([first.a.json.now,first.a.json.now[5:7],first.a.json.now[11:13],(map(.b.json.payload.battery_charging_current)| add/length),(map(.b.json.payload.yield_today)| add/length)]) | group_by(.[1]) | map({"mm":first[1],data:(.|sort_by(.[2])|map(.[3])),complete:(.|sort_by(.[2])|map(.[2])),"wh":(.|map(.[4])|max),"ah":(.|map(.[3])|add) })'  
```
This produces a JSON that shows the average of solar amps on a particular hour of the day, for every month.  .a.json.now[5:7],.a.json.now[11:13] represents the month, and hour, in the .now field.
<pre>
[
  {
    "mm": "07",
    "data": [
      0, 0, 0, 0, 0, 
      0.02722222222222222, 0.5783333333333336, 2.446368715083801,
      4.316666666666671, 6.395555555555556, 7.616759776536316,
      9.661142857142853, 10.994642857142859, 11.144936708860754,
      10.560135135135138, 10.355633802816898, 8.267187499999999,
      6.645985401459853, 3.747445255474453,
      1.6132911392405052, 0.3610465116279072,
      0.01420118343195267, 0, 0
    ],
    "complete": [ "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23" ],
    "wh": 1323.296089385475,
    "ah": 94.74655462173106
  }
]
</pre>



## Program: jqoin.py
"Inner Join" 2 different streams of JSON.  Correlating 2 different JSON, to single relationship

###You can supply just a directory as source of JSON, and parts of filename to correlate the object.  Theoretically this is fastest, but in practice I've seen no difference.  Probably bc the correlation algorithm I use, is probably unsophisticated and takes a long time, compared to the huge difference betwwen that is supposed to exist between reading filenames, and the contents of all the files.
```
./jqoin.py "renogy_json/renogy*" filename:6:19 "victron_json/victron*" filename:7:20
```
This will create a record for each file whose filenames match on char 6-19 and char 7-20, from each directory respectively.  This record will have .a field representing the first directory object, .b representing the 2nd directory object, and .key representing the part of the filename that matches for both files
<pre>
...
{"key": "240705_183001", 
 "a": {"filename": "renogy240705_183001.json", 
       "json": {"function": "READ", "cell_count": 4, "cell_voltage_0": 3.5, "cell_voltage_1": 3.5, "cell_voltage_2": 3.5, "cell_voltage_3": 3.5, "sensor_count": 2, "temperature_0": 24.0, "temperature_1": 24.0, "current": 0.0, "voltage": 14.200000000000001, "remaining_charge": 76.4, "capacity": 100.0, "model": "RBT100LFP12-BT", "__device": "BT-TH-66FA6197", "__client": "BatteryClient", "now": "2024/07/05 18:30:18"}}, 
 "b": {"filename": "victron240705_183001.json", 
       "json": {"name": "SmartSolar HQ191148API", "address": "DA:D6:19:7E:90:4F", "rssi": -61, "payload": {"battery_charging_current": 5.8, "battery_voltage": 14.4, "charge_state": "bulk", "external_device_load": 0.0, "model_name": "SmartSolar MPPT 100|20", "solar_power": 86, "yield_today": 1670}, "now": "2024/07/05 18:31:06"}}}
...
</pre>

###You can use fields inside JSON, to do correlation between fields inside the JSON
```
./jqoin.py "renogy_json/renogy*" .now:0:17 "victron_json/victron*" .now:0:17
```
This will create a record for each file whose .now field's first 17 characters (so it excludes the seconds value), with a, b, and the key which contains the matching part of the value in both directory's object's .now fields.
<pre>
...
{"key": "2024/07/30 23:10:", 
 "a": {"filename": "renogy_json/renogy240730_231001.json", 
       "json": {"function": "READ", "cell_count": 4, "cell_voltage_0": 3.2, "cell_voltage_1": 3.1, "cell_voltage_2": 3.2, "cell_voltage_3": 3.2, "sensor_count": 2, "temperature_0": 21.0, "temperature_1": 21.0, "current": -2.3000000000000003, "voltage": 12.8, "remaining_charge": 9.0, "capacity": 100.0, "model": "RBT100LFP12-BT", "__device": "BT-TH-66FA6197", "__client": "BatteryClient", "now": "2024/07/30 23:10:40"}}, 
 "b": {"filename": "victron_json/victron240730_231001.json", 
       "json": {"name": "SmartSolar HQ191148API", "address": "DA:D6:19:7E:90:4F", "rssi": -73, "payload": {"battery_charging_current": 0.0, "battery_voltage": 12.74, "charge_state": "off", "external_device_load": 0.0, "model_name": "SmartSolar MPPT 100|20", "solar_power": 0, "yield_today": 480}, "now": "2024/07/30 23:10:04"}}}
...
</pre>


###One of the JSON streams can be supplied by pipe redirection to stdin (but no filename match this way):
```
cat gpspipe_json/* | ./jqoin.py "iperf_json/" .now:0:17 --key=.time:0:17 
```
This will create a record for each object in gpspipe_json streamed in stdin, whose .now field's first 17 characters (so it excludes the seconds value), with a, b, and the key which contains the matching part of the value in iperf_json directory's object's .now fields.

<pre>
...
{"key": "2024-07-13T07:20:", 
 "a": {"filename": "iperf240713_002001.json", 
       "json"
: {"now": "2024-07-13T07:20:02Z", "send": 6290963.374042257, "recv": 4904836.670
335114}}, 
 "b": {"filename": "stdin", 
       "json": {"class": "TPV", "device": "/dev/tt
yUSB0", "status": 2, "mode": 3, "time": "2024-07-13T07:20:00.000Z", "ept": 0.005
, "lat": 49.227103333, "lon": -122.943355, "alt": 116.5, "epx": 2.076, "epy": 2.
409, "epv": 8.05, "track": 17.69, "speed": 0.067, "climb": 0, "eps": 4.82, "epc"
: 16.1}}}
...
</pre>



## Explanation of testdata
*gpspipe_json/* has gps data, multiple JSON objects per file

*iperf_json/* has speedtest data, 1 JSON object per file

*renogy_json/* has battery state of charge data, 1 JSON object per file

*victron_json/* has solar controller data, only the first JSON in file is relevant

jqjoin.py will accept multiple objects from stdin,
BUT only accepts first JSON object per file WHEN as directory argument.





