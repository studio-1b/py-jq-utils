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

## Program: groupbyjson.py
Write your own aggregate function.  But first, how you execute it:
```
./groupbyjson.py [groupby key 1]...[groupby key n] [json of aggregate]
```
It does NOT accept JSON array thru stdin, but a stream of JSON objects only delimited by close of a JSON object.

For example, avg, count and max are implemented, and can be used like:
```
victron_json/victron*.json | ./groupbyjson.py .now[5:7] .now[11:13] '{"mm":arg[0],"hh":arg[1],"a":avg(.payload.yield_today),"b":max(.payload.yield_today),"c":count(.now)}' 2>/dev/null
```
produces
<pre>
{"mm": "07", "hh": "00", "a": 1295.483870967742, "b": 1840, "c": 1116}
{"mm": "07", "hh": "01", "a": 887.5268817204301, "b": 1840, "c": 1116}
{"mm": "07", "hh": "02", "a": 56.12903225806452, "b": 1740, "c": 1116}
{"mm": "07", "hh": "03", "a": 37.41935483870968, "b": 1740, "c": 1116}
{"mm": "07", "hh": "04", "a": 0.0, "b": 0, "c": 1116}
{"mm": "07", "hh": "05", "a": 0.0, "b": 0, "c": 1116}
{"mm": "07", "hh": "06", "a": 3.3960573476702507, "b": 20, "c": 1116}
{"mm": "07", "hh": "07", "a": 21.962365591397848, "b": 60, "c": 1116}
{"mm": "07", "hh": "08", "a": 67.54480286738351, "b": 140, "c": 1116}
{"mm": "07", "hh": "09", "a": 138.34229390681003, "b": 270, "c": 1116}
{"mm": "07", "hh": "10", "a": 232.58960573476702, "b": 440, "c": 1116}
{"mm": "07", "hh": "11", "a": 350.92792792792795, "b": 630, "c": 1110}
{"mm": "07", "hh": "12", "a": 491.52329749103944, "b": 840, "c": 1116}
{"mm": "07", "hh": "13", "a": 644.6812386156648, "b": 1050, "c": 1098}
{"mm": "07", "hh": "14", "a": 793.8351254480286, "b": 1240, "c": 1116}
{"mm": "07", "hh": "15", "a": 932.6086956521739, "b": 1430, "c": 1104}
{"mm": "07", "hh": "16", "a": 1048.502824858757, "b": 1580, "c": 1062}
{"mm": "07", "hh": "17", "a": 1154.465579710145, "b": 1710, "c": 1104}
{"mm": "07", "hh": "18", "a": 1222.142857142857, "b": 1790, "c": 1092}
{"mm": "07", "hh": "19", "a": 1266.021505376344, "b": 1830, "c": 1116}
{"mm": "07", "hh": "20", "a": 1278.6021505376343, "b": 1840, "c": 1116}
{"mm": "07", "hh": "21", "a": 1276.7391304347825, "b": 1840, "c": 1104}
{"mm": "07", "hh": "22", "a": 1278.3783783783783, "b": 1840, "c": 1110}
{"mm": "07", "hh": "23", "a": 1279.8918918918919, "b": 1840, "c": 1110}
</pre>

"Group by" just segregates the data by the values you provide.  It is the same function as SQL's "group by".  Example groups by 2 values, substring of .now which gets month, and substring of .now which gets hour.  Once the data is segregated, you can apply aggregate functions to specific fields, and display them.  The example shows how to output each group in a separate JSON object.  The object's mm is filled from value in first groupbyjson argument(arg[0]), and hh field is filled with 2nd argument to groupbyjson(arg[1]).  a is the avg of yield for that hour and month, b is max, and c is count of records in that segregated bin.

However my version of groupbyjson.py runs extremely slow versus jq's implementation.  This is how to run the same group by in jq:
```
cat victron_json/victron*.json | jq -s '.|group_by(.now[5:7],.now[11:13]) | map([first.now[5:7],first.now[11:13],(map(.payload.yield_today)| max),(map(.payload.yield_today)| add/length)])' | jq -c '.[]'
```

<pre>
["07","00",1840,1295.483870967742]
["07","01",1840,887.5268817204301]
["07","02",1740,56.12903225806452]
["07","03",1740,37.41935483870968]
["07","04",0,0]
["07","05",0,0]
["07","06",20,3.3960573476702507]
["07","07",60,21.962365591397848]
["07","08",140,67.54480286738351]
["07","09",270,138.34229390681003]
["07","10",440,232.58960573476702]
["07","11",630,350.92792792792795]
["07","12",840,491.52329749103944]
["07","13",1050,644.6812386156648]
["07","14",1240,793.8351254480286]
["07","15",1430,932.6086956521739]
["07","16",1580,1048.502824858757]
["07","17",1710,1154.465579710145]
["07","18",1790,1222.142857142857]
["07","19",1830,1266.021505376344]
["07","20",1840,1278.6021505376343]
["07","21",1840,1276.7391304347825]
["07","22",1840,1278.3783783783783]
["07","23",1840,1279.8918918918919]
</pre>

However my groupbyjson.py is slower than jq
<pre>
bob@fedora:~/solarjson/victron_json$ date && cat victron*.json | jq -s '.|group_by(.now[5:7],.now[11:13]) | map([first.now[5:7],first.now[11:13],(map(.payload.battery_charging_current)| max),(map(.payload.battery_charging_current*24)| add/length),(map(.payload.yield_today)| max),(map(.payload.yield_today)| add/length)])' &>/dev/null && date
Mon Sep  2 05:28:46 PM PDT 2024
Mon Sep  2 05:29:08 PM PDT 2024

bob@fedora:~/solarjson/victron_json$ date && cat victron*.json | ../../groupbyjson.py .now[5:7] .now[11:13] '{"mm":arg[0],"hh":arg[1],"a":avg(.payload.yield_today),"b":max(.payload.yield_today),"c":count(.now)}'&>/dev/null && date
Mon Sep  2 05:30:43 PM PDT 2024
Mon Sep  2 05:32:52 PM PDT 2024
</pre>
Much slower.  6x slower.
jq    vs groupbyjson.py
25sec vs 2min

I admit I thought I could write a more competitive version of groupby, when jq ran so slow on my pi and sometimes crashed if too many groupby elements were included.  I thought I could write a faster version in python.  I could not.  But I got groupbyjson.py working.  There is value in keeping this code around.  If I ever need to implement my own aggregate function that jq does not support, even if 6x slower, 6x slower is better than thing.  You can add your own Aggregate functions too:

To add more aggregate functions, 
1. Add new classes by copying one of the Aggregate* classes
    A. change the identify() function, to the name of your new function
    B. isgoodarg() function, to statically validate the argument list.  Existing examples only validate the number of arguments.
    C. change clone(), to return a new instance of itself
    D. change add(), to implement the incremental steps aggregation function, with each new field value submitted to it
    E. change result(), to finalize the calculation and return the result, in any JSON compatible datatype
2. Modifying the JsonTransform class, in 2 places
    A. This is the most important step.  Adding the new class name in the
    array of classes that it will check if there is a function...
    ```
    SUPPORTED=[AggregateCount,AggregateSum,AggregateMin,AggregateMax, \
        AggregateAvg,AggregateStdev,AggregateStrAppend,AggregateLstAppend, \
        AggregateLinreg, **Add the new class name**
    ]
    ```
    B. Adding the name in the regex, in JsonTransform class's __init__: function.
    ```
        regex = r"(sum|avg|min|max|count|stdev|linreg**Add same name as 1A**)\(((\.[^,\s\)]+)(,.[^,\)\s]+)*)\)" 
    ```
    This function is just searching for a string that might be a function.  It is a shallow validation.  And used later to identify the functions in the output JSON, to later replace them




## Explanation of testdata
*gpspipe_json/* has gps data, multiple JSON objects per file

*iperf_json/* has speedtest data, 1 JSON object per file

*renogy_json/* has battery state of charge data, 1 JSON object per file

*victron_json/* has solar controller data, only the first JSON in file is relevant

jqjoin.py will accept multiple objects from stdin,
BUT only accepts first JSON object per file WHEN as directory argument.






