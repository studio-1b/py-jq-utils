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

import re


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


class FixedSlice:
    def __init__(self,a,b):
        self._a = a
        self._b = b
    def slice(self,s):
        a = self._a
        b = self._b
        if not type(s) is str:
            return None  # we are going to ignore an error here
        if a==None and b!=None:
            return s[0:self._b]
        if a==None and b!=None:
            return s[self._a:]
        if a!=None and b!=None:
            return s[self._a:self._b]
        else:
            return None  # again, this is error but ignoring

def key_to_keypath(key):
    path = key.split(".")
    pathL = len(path)
    if L<2:
        raise Exception("Not a json path:"+key)
    if path[0]!="":
        raise Exception("Not supported json path, must start with period:"+key)

    # check if key is computed field, first slice operator
    last = path[pathL-1]
    a=-1
    c=-1
    b=-1
    try:
        a = last.index("[")
    except:
        pass
    try:
        c = last.index(":")
    except:
        pass
    try:
        b = last.index("]")
    except:
        pass
    if a>0 and b>a:
        path[pathL-1] = last[0:a] # replace the key w/ function, with just key name
        # lets find the parameters of the function/operator [:]
        # append the function to the end of the path list of string keys, so it can be easily identified
        slice = last[a+1:b]
        if c<0 and slice[0:c-a].isdigit(): #[1]
            #return result[ int(slice) ]
            path.append(FixedSlice(int(slice),int(slice)+1))
        elif a<c and c<b:
            if a+1==c and c+1>b:  # [:b]
                slice = last[a+1:c]
                if slice.isdigit():
                    #return result[ 0:int(slice) ]
                    path.append(FixedSlice(None,int(slice)))
            elif a+1<c and c+1==b: # [a:]
                slice = last[c+1:b]
                if slice.isdigit():
                    #return result[ int(slice): ]
                    path.append(FixedSlice(int(slice),None))
            elif a+1<c and c+1<b: # [a:b]
                #print("a:b")
                slice1 = last[a+1:c]
                slice2 = last[c+1:b]
                #all1 = slice1.all(lambda ch: ch<='0' and ch<='9')
                #all2 = slice2.all(lambda ch: ch<='0' and ch<='9')
                if slice1.isdigit() and slice2.isdigit():
                    # return result[ int(slice1):int(slice2) ]
                    path.append(FixedSlice(int(slice1),int(slice2)))
            #this branch [:] should end with FixedSlice, otherwise error
            if len(path)<=pathL or not type(path[pathL]) is FixedSlice:
                print(a,c,b)
                print(slice)
                print(path)
                raise Exception("Slice syntax is wrong:" + last)
    elif a>=0 or b>=0 or c>=0:
        print(a,c,b)
        raise Exception("unexpected []"+last)
    return path[1:]

def get_keypath_lst(o,keylst):
    result = []
    for item in keylst:
        value = get_key_path(o,item)
        result.append(value)
    return result

def get_key(o,key):
#    print(key)
#    print(o)
    parts=key.split('.')
    return get_key_path(parts[1:])

def get_key_path(o,keypathlst):
#    print("Searching....")
#    print(o)
#    print("for....")
#    print(keypathlst)
    result=None
    parts=keypathlst
    L  = len(parts)
    if L>=1:
      for i in range(0,L):
        #print(i)
        #print(parts[i])
        next = parts[i]
        if type(next) is FixedSlice:
          return next.slice(o) # risk confusion, bc operators only on "leaf", so this SHOULD BE last item
        if next in o:
          o = o[next]
          result = o #result[parts[i]]
        else:
          result=None
          break
      return result
    else:
      return None

def set_keypath(o,keypath,value):
#    print(key)
#    print(o)
    parts=keypath
    L  = len(parts)
    lookup = None
    for i in range(0,L-1):
        #print(i)
        #print(parts[i])
        lookup = parts[i]
        if lookup in o:
            o = o[lookup]
        else:
            newkey={}
            o[lookup] = newkey
            o = newkey
    lookup = parts[L-1]
    o[lookup] = value  #add and update single value is same syntax


class AggregateSum:
    @staticmethod
    def identify(str):
        return str=="sum"
    def isgoodarg(lst):
        return len(lst)==1

    def __init__(self):
        self._sum=0
        #self.list=[]
    def clone(self):
        return AggregateSum()
    def add(self,item):
        self._sum+=item[0]
        #self.list.append(item)
    def result(self):
        return self._sum

class AggregateCount:
    @staticmethod
    def identify(str):
        return str=="count"
    def isgoodarg(lst):
        return len(lst)==1

    def __init__(self):
        self._count=0
        #self.list=[]
    def clone(self):
        return AggregateCount()
    def add(self,item):
        if item!=None:
            self._count+=1
        #self.list.append(item)
    def result(self):
        return self._count

class AggregateMax:
    @staticmethod
    def identify(str):
        return str=="max"
    def isgoodarg(lst):
        return len(lst)==1

    def __init__(self):
        self._max=None
        #self.list=[]
    def clone(self):
        return AggregateMax()
    def add(self,item):
        if item!=None and item[0]!=None:
            arg=item[0]
            if self._max==None:
                self._max=arg
            elif arg>self._max:
                self._max=arg
        #self.list.append(item)
    def result(self):
        return self._max

class AggregateMin:
    @staticmethod
    def identify(str):
        return str=="min"
    def isgoodarg(lst):
        return len(lst)==1

    def __init__(self):
        self._min=None
        #self.list=[]
    def clone(self):
        return AggregateMin()
    def add(self,item):
        if item!=None and item[0]!=None:
            arg=item[0]
            if self._min==None:
                self._min=arg
            elif self._min<arg:
                self._min=arg
        #self.list.append(item)
    def result(self):
        return self._min

class AggregateAvg:
    @staticmethod
    def identify(str):
        return str=="avg"
    def isgoodarg(lst):
        return len(lst)==1

    def __init__(self):
        self._count=0
        self._sum=0
        #self.list=[]
    def clone(self):
        return AggregateAvg()
    def add(self,item):
        if item!=None and item[0]!=None:
          self._count+=1
          self._sum+=item[0]
    def result(self):
        return  self._sum/self._count
class AggregateStdev:
    @staticmethod
    def identify(str):
        return str=="stdev"
    def isgoodarg(lst):
        return len(lst)==1

    def __init__(self):
        self._list=[]
        self._mean = AggregateAvg()
        #self.list=[]
    def clone(self):
        return AggregateStdev()
    def add(self,item):
        if item!=None and item[0]!=None:
            arg=item[0]
            self._list.append(arg)
            self._mean.add(iarg)
    def result(self):
        mean=self._mean.result()
        return math.sqrt(reduce(lambda s,i: s+math.sqr(mean-i),self._list)/len(self._list))

class AggregateLinreg:
    @staticmethod
    def identify(str):
        return str=="linreg"
    def isgoodarg(lst):
        return len(lst)==2

    def __init__(self):
        raise Exception("Not implemented")
        self._count=0
        #self.list=[]
    def clone(self):
        return AggregateLinreg()
    def add(self,item):
        if item!=None:
            self._count+=1
        #self.list.append(item)
    def result(self):
        return self._count

class AggregateLstAppend:
    @staticmethod
    def identify(str):
        return str=="append"
    def isgoodarg(lst):
        return len(lst)==1

    def __init__(self):
        self._lst=[]
        #self.list=[]
    def clone(self):
        return AggregateLstAppend()
    def add(self,item):
        if item!=None:
            self._lst.append(item[0])
        #self.list.append(item)
    def result(self):
        return self._lst

class AggregateStrAppend:
    @staticmethod
    def identify(str):
        return str=="append"
    def isgoodarg(lst):
        return len(lst)==1

    def __init__(self):
        self._worker = AggregateLstAppend()
        #self.list=[]
    def clone(self):
        return AggregateStrAppend()
    def add(self,item):
        self._worker.add( item )
    def result(self):
        return ''.join( self._worker.result() )


class FunctionRecord:
    def __init__(self, extractlist, aggregator, destKey):
        self._extractlist = extractlist
        self._aggregator = aggregator
        self._destKey = destKey
    def extractlist(self):
        return self._extractlist
    def aggregator(self):
        return self._aggregator
    def destKey(self):
        return self._destKey
    def clone(self):
        return FunctionRecord(self._extractlist, self._aggregator.clone(), self._destKey)

class JsonTransform:
    SUPPORTED=[AggregateCount,AggregateSum,AggregateMin,AggregateMax, \
        AggregateAvg,AggregateStdev,AggregateStrAppend,AggregateLstAppend, \
        AggregateLinreg
    ]
    def __init__(self, transform):
        self._transform = transform
        if transform==None:
            self._loaderror=3
            self._keys=None
            return
        self._loaderror = 3  #unintelligible

        self._keys={}
        #regex = r"(sum|avg|min|max|count|stdev|linreg)\((\.\S\S*)\)\[(\.[^,\s]+)(,[^,\s]+)*\]"
        regex = r"(sum|avg|min|max|count|stdev|linreg)\(((\.[^,\s\)]+)(,.[^,\)\s]+)*)\)"

        syntaxgood = re.sub(regex, "null", transform)
        if syntaxgood!=transform:
            self._loaderror = 2  # at least some recognizeable functions
        arg_regx = r"arg\[[0-9]+\]"
        syntaxgood = re.sub(arg_regx, "null", syntaxgood)
        try:
            self._obj = json.loads( syntaxgood )
            self._loaderror = 1 # valid jason
        except Exception as ex:
            print("without the functions, the result isn't a json")
            print( syntaxgood )
            exit(1)

        declarations = []
        reducetype = None
        tmp = transform
        fnarg = re.search(regex, tmp)
        while fnarg !=None:
            aggregator = None
            dest = fnarg[0]
            fntext = fnarg[1]
            keycsv = fnarg[2]
            for reducefn in JsonTransform.SUPPORTED:
                if reducefn.identify( fntext ):
                    reducetype = reducefn
                    aggregator = reducetype()
                    break
            if aggregator==None:
                raise Exception("Unknown function:"+fntext)

            #print( fntext )
            #print( keycsv )
            unparsedkeys = keycsv.split(",")
            keys = list( map(lambda s:   key_to_keypath(s), unparsedkeys) )
            fnparmL=len(keys)
            # fnparmL==0 is impossible b/c of regex
            if not reducetype.isgoodarg(keys):
                raise Exception("Wrong number of arguments(" +str(fnparmL)+ ") for:"+fntext + " : " + keycsv)
            # we need 1) aggregator 2) argumentlist 3) position in transfor
            # destKEYS is JSON path in transform where we found the function
            work = FunctionRecord(keys, aggregator, dest)
            declarations.append(work)

            # look for next function
            starting = fnarg.span()[1]
            tmp = tmp[starting:]
            fnarg = re.search(regex, tmp)

        # for each function in transform
        self._keys = declarations
        #self._keys is actually the list of aggregate counters
#        for item in declarations:
#            print(item.extractlist())
#            print(item.aggregator())
#            print(item.destKey())

    def clone(self,replaceargs):
        copy = JsonTransform(None)
        copy._transform = self._transform
        if replaceargs!=None:
            i=0
            replacewithjson = list( map(lambda s: json.dumps(s),replaceargs) )
            for item in replacewithjson:
                copy._transform = copy._transform.replace("arg["+str(i)+"]",item)
                i+=1
        #copy._keys = self._keys #new instances required of aggregator
        copy._keys = list( map(lambda s: s.clone(),self._keys) )
        return copy
    def loaderror(self):
        return self._loaderror;
    def add(self,json):
        for item in self._keys:
            valuesforfunction = item.extractlist()
            paramvalues = get_keypath_lst(json, valuesforfunction)
            item.aggregator().add(paramvalues)
    def result(self):
        # how do we replace the nodes in dictionary, with the values?
        countersforgroup = self._keys
        outjson = self._transform
        for item in countersforgroup:
            logicmodule = item.aggregator()
            fieldsforlogic = item.extractlist()
            logicresult = logicmodule.result()
            searchfor = item.destKey()
            #print( logicmodule,fieldsforlogic,logicresult )
            outjson = outjson.replace(searchfor,str(logicresult))
        #return self._keys
        #print( outjson )
        return json.loads( outjson )

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def show_groupby_result(result,level):
    indent = " " * (level*4)
    if type(result) is dict:
       for key in result:
           eprint( indent,key )
           show_groupby_result(result[key],level+1)
    else:
        sys.stderr.write( indent )
        print( json.dumps(result.result()) )



L = len(sys.argv)
if L < 3:
    print("Usage: | groupbyjson.py [group by key1] ... [group by keyn] [aggregate transform]")
    print("   echo '{\"date\":\"2024/08/01\",\"region\":\"ny\",\"sale\":10}' \\")
    print("        | groupbyjson.py '.date[5:7]' '.region' \\")
    print("                         '{\"mm\":.date[5:7], \"region\":.region, \"avg\":avg(.sale)}'")
    print("   {\"mm\":\"08\", \"region\":\"ny\", \"avg\":10)")
    print("")
    print("")
    exit(1)


#m = re.search( r"(sum|avg|min|max|count|stdev|linreg)\((\.\S\S*)\)\[(\.[^,\s]+)(,[^,\s]+)*\]", sys.argv[L-1] )
#m = re.search( r"(sum|avg|min|max|count|stdev|linreg)\((\.[^,\s]+)(,.[^,\)\s]+)*\)", sys.argv[L-1] )
#print( m )
#print( m[0] )
#print( m[1] )
#print( m[2] )
#print( m[3] )
#exit(2)

# this branch loads the files into memory, processes joins
is_pipe = not isatty(sys.stdin.fileno())
if is_pipe:
    groups = {}
    lst = []

    keys = sys.argv[1:L-1] #does not include L-1
    keypaths = list( map(lambda s:key_to_keypath(s),keys) )
    transform = sys.argv[L-1]
    prototype = JsonTransform(transform)

    #value = map(lambda s: {"origin":{"lat":lat,"lon":lon}, "lat":s["lat"], "lon":s["lon"], "dist":calc_distance(gpx,s)}, get_stdin())
    count=0
    num_groups=0
    try:
        for item in get_stdin():
            count+=1
            #print("--new--")
            # sys.stderr.write("\r" + count)
            # finding the set that this record belongs to
            groupbyvalues = get_keypath_lst(item,keypaths)
            bincollector = get_key_path(groups,groupbyvalues)
            #print(groupbyvalues)
            #print(groups)
            #try:
            #    print(groups[groupbyvalues[0]])
            #    print(bincollector)
            #except:
            #    pass
            if bincollector==None:
                num_groups+=1
                bincollector = prototype.clone(groupbyvalues) # clone, but replace arg[?] in transform w/ groupby arg
                lst.append(bincollector)
                set_keypath(groups, groupbyvalues, bincollector)
            # apply this record to the set
            bincollector.add(item)
            #print( json.dumps(item) )
            # sys.stdout.flush()
    except KeyboardInterrupt:
        pass

    eprint("count:", count)
    eprint("groups:", num_groups)
    show_groupby_result(groups, 0)
    #print("are the addresses all the same")
    #for item in lst:
    #    print(item)
    exit(0)
else:
    sys.stderr.write("no data\n")
    exit(1)

