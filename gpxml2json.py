# This is a sample Python script.
'''
Read .xml created by gpspipe,
write to JSON file

parameters(-field:m:n,jsonfile, xmlfile1, xmlfile2)
  "-field:" is argument to divide files, group by substring of field
         :m start of field at m
         :n end of field, starting at m, length n

When processing just 1 input xml file, this program operates in single thread operation.

This program does use multi-threading when processing more than 1 input file,
but I dont see any improvement.  Each input file is read in separate thread,
each thread buffers it's own output in Buffer object,
and main thread outputs each thread's output, in order that it was added as a thread,
as the thread finishes.  If later threads finish early, main thread will flush the output,
after the earlier thread's output is flushed.  This way the output is orderly, in order
that the files are read.

It is likely, too many little files burden the OS, and too much time is waiting for
the file reads to return data.
'''
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

# needed for arg processing and write to stderr
import sys
from traceback import format_exc

import select

# needed for list of files
import os
import threading
import glob
import multiprocessing

# needed for xml parsing
import xml.sax
import io

# needed for JSON serialization
import json as JSON

# needed if output is buffered
from io import StringIO

# needed to check parent path exists
from pathlib import Path

# needed to timer
from datetime import datetime


def debug(text):
    #print(text)
    pass

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
def ewrite(*args, **kwargs):
    print(*args, file=sys.stderr,end="", **kwargs)

def is_stdin_present():
    """
    Checks if data is available in stdin.
    """
    if os.name == 'nt':
        return not os.isatty(sys.stdin.fileno())
    else:
        return select.select([sys.stdin], [], [], 0)[0]
def read_stdin():
    """
    Reads data from stdin if available.
    """
    if is_stdin_present():
        return sys.stdin.read()
    else:
        return None





# make private routine
# thisdict = {
#   "brand": "Ford",
#   "model": "Mustang",
#   "year": 1964
# }
# <trkpt lat="29.179970" lon="-102.956875">
#     <ele>564.107368</ele>
#     <time>2017-04-10T15:27:02.000Z</time>
#     <src>GPSD tag=""</src>
def new_trkpt_json(lat, lon, ele, time, src, fix):
   return {"lat": lat, "lon":lon, "ele":ele, "time":time, "src":src, "fix":fix}


# make def, and add to contructor
class OutputDump():
    def __init__(self, filename=None):
        debug("STDOUT output")

    def dump(self,text,key=None):
        print(text)
    def serialize(self,obj):
        json = JSON.dumps(obj)
        self.dump(json)
    def flush(self):
        pass # do nothing, bc this is unbuffered
    def close(self):
        #print("{\"done\":1}")
        pass
class FileDump(OutputDump):
    def __init__(self, filename):
        # OutputDump.__init__(filename)
        self.filename = filename
        self.stream = open(filename, "w")
    def dump(self,text,key=None):
        self.stream.write(text)
    def serialize(self,obj):
        json = JSON.dumps(obj)
        self.dump(json)
    def close(self):
        self.stream.close()
class GroupDump(OutputDump):
    def __init__(self, filename, group, autoflush=True):
        self.autoflush = autoflush
        self.outbuffer = {}
        # OutputDump.__init__(filename)
        self.filename = filename
        self.streamlist = {}
        # group = "--name:start:len"
        self.group = group
        self.groupfield = None
        self.groupstart = None
        self.groupend = None
        self.groupfn = None
        parts = group[2:].split(":")
        l=len(parts)
        if (l>0):
            self.groupfn = self.nameonly
            self.groupfield = parts[0]
            if parts[0].isspace():
                print("No field name (lat,lon,ele,time,src,fix) given, between -- and end of switch in ("+group[2:]+")")
                exit(20)
        if (l>1):
            self.groupfn = self.endswith
            try:
                self.groupstart = int(parts[1])
            except ValueError:
                print("start index of group-by field, not a number (ie. --time:0:10): " + parts[1] + " in ("+group[2:]+")")
                exit(21)
        if (l>2):
            self.groupfn = self.column
            try:
                self.groupend = int(parts[2])
            except ValueError:
                print("length of group-by field, not a number (ie. --time:0:10): " + parts[2] + " in (" + group[2:]+")")
                exit(22)
    def nameonly(self,obj):
        return obj[self.groupfield]
    def endswith(self,obj):
        return obj[self.groupfield][self.groupstart:]
    def column(self,obj):
        k=obj[self.groupfield][self.groupstart:self.groupend]
        return obj[self.groupfield][self.groupstart :self.groupend]

    def dump(self, text, key):
        # key = self.groupfn(obj)
        if key == None:
            key = "_object_"
        stream = None
        lst = self.streamlist
        if key not in lst:
            basename, ext = os.path.splitext(self.filename)
            filename = basename + key + ".gpx." + ext[1:]
            ewrite("\r Creating " + filename + "  ")
            try:
                stream = open(filename, "w")
                lst[key] = stream
            except Exception as ex:
                print(basename)
                print(key)
                print(ext)
                print(filename)
                raise ex
        else:
            stream = lst[key]
        stream.write(text)
    def serialize(self, obj):
        key = self.groupfn(obj)
        if key == None:
            key = "_object_"
        json = JSON.dumps(obj)
        self.dump(json, key)
    def close(self):
        lst = self.streamlist
        for key in lst:
            lst[key].close()
class BufferedDump():
    def __init__(self, dumpsink):
        # print("buffer writes")
        self.outbuffer = StringIO()
        self.dumpsink = dumpsink
        # support GroupDump dumpsink
        self.outdict = {}
        if hasattr(dumpsink, "groupfn"):
            self.groupfn = dumpsink.groupfn
        else:
            self.groupfn = None
    def dump(self,text,key=None):
        if key == None:
            self.outbuffer.write(text)
        # support GroupDump dumpsink
        else:
            lst = self.outdict
            if key not in lst:
                lst[key] = StringIO()
            else:
                lst[key].write(text)

    def serialize(self,obj):
        json = JSON.dumps(obj)
        if self.groupfn==None:
            self.dump(json, None)
        # support GroupDump dumpsink
        else:
            key = self.dumpsink.groupfn(obj)
            if key == None:
                key = "_object_"
            json = JSON.dumps(obj)
            self.dump(json, key)

    def flush(self):
        if self.groupfn == None:
            self.dumpsink.dump(self.outbuffer.getvalue())
            self.outbuffer = StringIO()
        # support GroupDump dumpsink
        else:
            lst = self.outdict
            for key in lst:
                try:
                    self.dumpsink.dump(lst[key].getvalue(), key)
                except Exception as ex:
                    print(key)
                    print(lst)
                    raise ex
            self.outdict = {}
    def close(self):
        self.dumpsink.close()



'''
<gpx version="1.1" creator="GPSD 3.11 - http://catb.org/gpsd"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns="http://www.topografix.com/GPX/1/1"
        xsi:schemaLocation="http://www.topografix.com/GPX/1/1
        http://www.topografix.com/GPX/1/1/gpx.xsd">
 <metadata>
  <time>2017-04-10T15:27:02.000Z</time>
 </metadata>
 <trk>
  <src>GPSD 3.11</src>
  <trkseg>
   <trkpt lat="29.179970" lon="-102.956875">
    <ele>564.107368</ele>
    <time>2017-04-10T15:27:02.000Z</time>
    <src>GPSD tag=""</src>
    <fix>3d</fix>
   </trkpt>
  </trkseg>
 </trk>
 <trk>
  <src>GPSD 3.11</src>
  <trkseg>
   <trkpt lat="29.179979" lon="-102.957106">
    <ele>570.560371</ele>
    <time>2017-04-10T15:41:05.000Z</time>
    <src>GPSD tag=""</src>
    <fix>3d</fix>
   </trkpt>
   <trkpt lat="29.180063" lon="-102.957307">
    <ele>570.327112</ele>
    <time>2017-04-10T15:41:10.000Z</time>
    <src>GPSD tag=""</src>
    <fix>3d</fix>
   </trkpt>
  </trkseg>
 </trk>
'''
class GpspipeXmlHandler(xml.sax.ContentHandler):
    def __init__(self, sink):
        self.sink = sink

        self.last_tag = ""

        self.is_metadata = False
        self.is_trk = False
        self.is_trkseg = False
        self.is_trkspt = False

        self.trkspt = None

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.last_tag = tag
        if tag == "metadata":
            debug("*****metadata*****")
            #title = attributes["title"]
            self.is_metadata = True
        elif tag == "time":
            debug("*****time*****")
        elif tag == "trk":
            debug("*****trk*****")
            self.is_trk = True
        elif tag == "src":
            debug("*****src*****")
        elif tag == "trkseg":
            debug("*****trkseg*****")
            self.is_trkseg = True
        elif tag == "trkpt":
            debug("*****trkpt*****")
            lat = attributes["lat"]
            lon = attributes["lon"]
            self.trkspt = new_trkpt_json(float(lat), float(lon), None, "", "", "")
            self.is_trkspt = True
        elif tag == "ele":
            debug("*****ele*****")
        elif tag == "time":
            debug("*****time*****")
        elif tag == "src":
            debug("*****src*****")
        elif tag == "fix":
            debug("*****fix*****")


    # Call when an elements ends
    def endElement(self, tag):
        self.last_tag = tag
        debug("END "+tag)
        if tag=="fix" or tag=="src" or tag=="time" or tag=="ele" :
            pass # ignore close tags for these
        elif self.is_trkspt:
            self.is_trkspt = False
            # write to self.last_tag
            self.sink.serialize(self.trkspt)
            self.trkspt = None
        elif self.is_trkseg:
            self.is_trkseg = False
        elif self.is_trk:
            self.is_trk = False
        elif self.is_metadata:
            self.is_metadata = False

    # Call when a character is read
    def characters(self, content):
        debug("chars")
        debug(self.is_trkspt)
        debug(content.isspace())
        if self.is_trkspt and not content.isspace():
            current = self.trkspt
            if self.last_tag == "ele":
                debug("*****trkpt.ele inner*****" + content)
                try:
                    current["ele"] = float(content)
                except ValueError:
                    pass #ignore
            elif self.last_tag == "time":
                debug("*****trkpt.time inner*****")
                current["time"] += content
            elif self.last_tag == "src":
                debug("*****trkpt.src inner*****")
                current["src"] += content.replace(" tag=\"\"", "")
            elif self.last_tag == "fix":
                debug("*****trkpt.fix inner*****")
                current["fix"] += content





class StringXmlParser():
    def __init__(self, text, sink):
        self.text = text
        self.sink = sink

        # create an XMLReader
        #parser = xml.sax.make_parser()
        # turn off namepsaces
        #parser.setFeature(xml.sax.handler.feature_namespaces, 0)
        # override the default ContextHandler
        Handler = GpspipeXmlHandler(sink)
        #parser.setContentHandler(Handler)
        self.handler = Handler
    def parse(self):
        try:
            xml.sax.parseString(self.text, self.handler)
        except:
            pass
    def flush(self):
        self.sink.flush()
class FileXmlParser():
    def __init__(self, filename, sink):
        self.filename = filename
        self.sink = sink
        # create an XMLReader
        parser = xml.sax.make_parser()
        # turn off namepsaces
        parser.setFeature(xml.sax.handler.feature_namespaces, 0)
        # override the default ContextHandler
        Handler = GpspipeXmlHandler(sink)
        parser.setContentHandler(Handler)
        self.handler = Handler
        self.parser = parser
    def parse(self):
        try:
            self.parser.parse(self.filename)
        except:
            pass # empty file, not xml, ignore for now, unless user wants to know which files have errors
    def flush(self):
        self.sink.flush()





MAX_THREADS = multiprocessing.cpu_count()-1
global_thread_count=0
def start_job(bgworker, threadlist, workerlist, finished_count):
    #t = threading.Thread(target=bgworker.parse, args=())
    #threadlist.append(t)
    #t.start()
    global global_thread_count
    if global_thread_count<MAX_THREADS:
        a = len(threadlist)
        b = len(workerlist)
        while global_thread_count < MAX_THREADS and a<b:
            bgworker = workerlist[a]
            t = threading.Thread(target=bgworker.parse, args=())
            threadlist.append(t)
            t.start()
            global_thread_count+=1
            a = len(threadlist)
            b = len(workerlist)
    if not threadlist[finished_count].is_alive():
        workerlist[finished_count].flush()
        finished_count += 1
        global_thread_count -=1
    return finished_count

def assign_file_to_worker(inputarg, is_threaded, sink, read_workers):
    if os.path.isfile(inputarg):
        workersink = BufferedDump(sink.dumpsink) if is_threaded else sink
        bgworker = FileXmlParser(inputarg, workersink)
        read_workers.append(bgworker)
        return bgworker
    else:
        return None


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    debug(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')


    # total arguments
    n = len(sys.argv)
    if n == 0:
        print("\nName of Python script:", sys.argv[0])
        print("Usage: script [--field:m:n, jsonfile, xmlfile1, xmlfile2] ")
        print("output [jsonfile] mandatory")
        print("input  (optional)  [xmlfile] one or multiple, as many as you want, or none if data sent thru stdin")
        print("switches --fieldname      ...groups records in files suffixed with fieldname")
        print("switches --fieldname:4    ...groups records in files suffixed with fieldname substring starting with 4")
        print("switches --fieldname:2:5  ...groups records in files suffixed with fieldname substring starting with 2, end before 5")
        exit(1)
    switches = []
    argn = n
    arg = []
    for item in sys.argv:
        if item[0:2] == "--":
            argn-=1
            switches.append(item)
        else:
            arg.append(item)
    if (argn <= 1): # 1 arg is really no arg
        print("\nName of Python script:", sys.argv[0])
        print("Usage: "+sys.argv[0]+" [-field:m:n] [jsonfile] [xmlfile1] [xmlfile2] ")
        print("At least the output [jsonfile] name has to be provided")
        print(sys.argv[0]+" [output.json] [xmlfile1] ...read xmlfile1, output to output.json")
        print(sys.argv[0]+" - [xmlfile1] ...read xmlfile1, output to stdout")
        print("cat xmlfile1 |" +sys.argv[0] + " -  ...read stdin, output to stdout")
        print("cat xmlfile1 |" +sys.argv[0] + " output.json xmldir2/*.json ...read stdin,read xmldir2/xmldir2/*.json, output to output.json")
        exit(2)


    # produce readers
    sink = OutputDump()
    read_workers = []

    # check stdin is used, assign a reader for stdin
    stdin_ndx = -1
    pipein = read_stdin()
    if pipein!=None:
        read_workers.append(StringXmlParser(pipein, sink))
        stdin_ndx = 0

    # validate arguments, for expected output
    # if more than 1 producer, then multi-thread read, single queue out
    if (argn >= 2):
        filename = arg[1]
        if filename != "-":
            if (len(switches)==0):  # if stdout, then switches are irrelevant
                # file output, no groups b/c no switches
                if os.path.isfile(filename):
                    isover=input("Output file exists, do you wish to overwrite(y/n) " + filename +":")
                    if (isover!="y" and isover!="Y"):
                        print("Aborted!")
                        exit(3)
                sink = FileDump(filename)
                # update stdin reader (it is only reader defined, so far)
                if stdin_ndx==0: # unbuffered file output, for stdin out
                    read_workers[stdin_ndx] = StringXmlParser(pipein, sink)
            else:
                # filter switches, only for group format
                groupby = switches[-1]
                if len(switches) != 1:
                    eprint("only last switch used (out of "+str(len(switches))+"): " + groupby)
                # speculate, if output might overwrite
                basename, ext = os.path.splitext(filename)
                pattern = basename+"*.gpx."+ext[1:]
                search = glob.glob(pattern)
                if search!=None and len(search)>0:
                    isover=input("Possibilty of overwriting " + pattern + "("+str(len(search))+"files), do you wish to continue(y/n):" + filename)
                    if (isover != "y" and isover != "Y"):
                        print("Aborted!")
                        exit(4)
                sink = GroupDump(filename, groupby)
                # update stdin pipeline (it is only reader defined, so far)
                if stdin_ndx == 0:  # unbuffered file output, for stdin out
                    read_workers[stdin_ndx] = StringXmlParser(pipein, sink)

    # revalidate arguments, to check expected inputs
    bgworker = None
    if (pipein!=None and argn == 1): # 2 arg, is really 1 arg
        pass
        # echo '"'<xml>'"' |arg[0], is ok
    if (pipein==None and argn == 1): # 2 arg, is really 1 arg
        print("\nName of Python script:", arg[0])
        print("Usage: " + arg[0] + "[-field:m:n, jsonfile, xmlfile1, xmlfile2] ")
        print("No input data.  No stdin.  No input xml listed.")
        print("No output data.  No json, listed as output")
        print("Invalid: " + arg[0] + "")
        exit(5)
    if (pipein==None and argn == 2 and arg[1]=="-"): # 2 arg, is really 1 arg
        ("\nName of Python script:", arg[0])
        print("Usage: " + arg[0] + "[-field:m:n, jsonfile, xmlfile1, xmlfile2] ")
        print("No input data.  No stdin.  No xml listed.  Only stdout indicated")
        print("Invalid: " + arg[0] + " -")
        exit(6)
    if (not isinstance(sink, OutputDump) and not os.path.isfile(arg[1]) ):
        outpath = Path(arg[1])
        if not os.path.isdir(outpath.parent.absolute()):
            ("\nName of Python script:", arg[0])
            print("Usage: " + arg[0] + "[-field:m:n, jsonfile, xmlfile1, xmlfile2] ")
            print("Invalid: " + arg[1] + " doesn't seem to have valid directory, for output")
            exit(7)

    start = datetime.now()

    # determine if threading can help with multiple file reads
    is_threaded = False
    if (pipein!=None and argn > 2) \
    or (pipein==None and argn > 3) \
    or (os.path.isdir(arg[2])) \
    or ('*' in arg[2]) \
    or ('?' in arg[2]):
        sink = BufferedDump(sink) # multi-threaded ready
        is_threaded = True
        if stdin_ndx == 0:  # update stdin reader to be buffered
            read_workers[stdin_ndx] = StringXmlParser(pipein, sink)
    job_threads = []
    if (is_threaded and pipein!=None):
        bgjob = read_workers[stdin_ndx]
        t = threading.Thread(bgjob.parse, args=(bgjob))
        job_threads.append(t)
        t.start()

    # process each input argument, with read_worker AND IF THREADED ALSO A THREAD
    separator = os.sep
    outcounter = 0
    for inputarg in arg[2:]:
        if os.path.isfile(inputarg):
            reader = assign_file_to_worker(inputarg, is_threaded, sink, read_workers)
            if reader!=None and is_threaded:
                outcounter = start_job(reader, job_threads, read_workers, outcounter)
            ewrite("\r[" + str(len(read_workers)) + "] " + str(outcounter) + " " + inputarg + "      ")

        elif os.path.isdir(inputarg):
            pfix = inputarg
            for item in os.listdir(inputarg):
                reader = assign_file_to_worker(pfix +separator+ item, is_threaded, sink, read_workers)
                if reader != None and is_threaded:
                    outcounter = start_job(reader, job_threads, read_workers, outcounter)
                ewrite("\r[" + str(len(read_workers)) + "] " + str(outcounter) + " " + item + "      ")
        elif ('*' in inputarg or '?' in inputarg):
            good = glob.glob(inputarg)
            if good != None:
                for item in good:
                    # argpath = Path(inputarg)
                    # pfix = str(argpath.parent.absolute())
                    reader = assign_file_to_worker(item, is_threaded, sink, read_workers)
                    if reader != None and is_threaded:
                        outcounter = start_job(reader, job_threads, read_workers, outcounter)
                    ewrite("\r[" + str(len(read_workers)) +"] "+ str(outcounter) +" "+ item + "      ")
        else:
            print("not file or directory or glob, why didn't validations catch it " + inputarg)
            exit(10)

    if is_threaded:
        file_count = str(len(read_workers))
        while outcounter<len(job_threads):
            job_threads[outcounter].join()  # wait until finished
            read_workers[outcounter].flush()
            outcounter += 1
            global_thread_count -=1
            pad = 79-len(file_count + " [" + str(outcounter) + "] ....Working....")
            ewrite("\r" + file_count + " [" + str(outcounter) + "] ....Working...." + (" "*pad))
            # create new threads, as old ones finish
            a = len(job_threads)
            b = len(read_workers)
            while global_thread_count < MAX_THREADS and a < b:
                bgworker = read_workers[a]
                t = threading.Thread(target=bgworker.parse, args=())
                job_threads.append(t)
                t.start()
                global_thread_count += 1
                a = len(job_threads)
                b = len(read_workers)
    else:
        for item in read_workers:
            item.parse()

    eprint("")
    eprint("files processed: " + str(len(read_workers)) )

    end = datetime.now()
    eprint("in : " + str(end.timestamp()-start.timestamp()) + "sec")

    sink.close()
    exit(0)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/


