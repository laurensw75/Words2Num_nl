#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
import json
import sys
import re

number_blocks = [
    'biljoen', 'miljard', 'miljoen', 'duizend', 'honderd'
]

digits = [
    'één', 'twee', 'drie', 'vier', 'vijf', 'zes', 'zeven', 'acht', 'negen', 'nul', 'tien', 'elf', 'twaalf', 'dertien', 'veertien', 'vijftien', 'zestien', 'zeventien', 'achttien', 'negentien'
]

decades = [
    'twintig', 'dertig', 'veertig', 'vijftig', 'zestig', 'zeventig', 'tachtig', 'negentig'
]

dnb=digits+number_blocks
dd=digits+decades

getallen = {
    'nul': 0,
    'en': 0,
    'één': 1,
    'twee': 2,
    'drie': 3,
    'vier': 4,
    'vijf': 5,
    'zes': 6,
    'zeven': 7,
    'acht': 8,
    'negen': 9,
    'tien': 10,
    'elf': 11,
    'twaalf': 12,
    'dertien': 13,
    'veertien': 14,
    'vijftien': 15,
    'zestien': 16,
    'zeventien': 17,
    'achttien': 18,
    'negentien': 19,
    'twintig': 20,
    'dertig': 30,
    'veertig': 40,
    'vijftig': 50,
    'zestig': 60,
    'zeventig': 70,
    'tachtig': 80,
    'negentig': 90,
    'honderd': 100,
    'duizend': 1000,
    'miljoen': 1000000,
    'miljard': 1000000000,
    'biljoen': 1000000000000
}

looked=False
line=''

class Transcript:

    def __init__(self):
        self.words = []
        self.ident = ''
        self.event = ''
        self.channel = []
        self.start = []
        self.duration = []
        self.pp = []
        self.result = []
        self.offset = []
        self.valid = False

    def isValid(self):
        return self.valid

    def __byteify(self, input):
        if isinstance(input, dict):
            return {byteify(key): byteify(value)
                    for key, value in input.iteritems()}
        elif isinstance(input, list):
            return [byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input

    def readInput(self):
        global looked
        global line

        if not looked:
            line = sys.stdin.readline()
        else:
            looked = False
        if not line:
            self.valid = False
            return

        self.valid = True

        while re.match(r'^(\S+)\s+\S+\s+[0-9.]+\s+[0-9.]+\s+\S+(\s+[0-9.]+)?$', line):
            # For a CTM file read all lines with the same file descriptor (column 1)
            parts = line.strip().split()
            if (not self.ident) or (parts[0] == self.ident):
                # treat the ctm as a single line for each identifier string
                self.ident = parts[0]
                self.channel.append(parts[1])
                self.start.append(float(parts[2]))
                self.duration.append(float(parts[3]))
                self.words.append(parts[4])
                if len(parts) > 5:
                    self.pp.append(float(parts[5]))
                line = sys.stdin.readline()
                if not line:
                    break
            else:
                # new identifier
                looked = True
                break

        if not self.ident:
            # file is either JSON or plaintext
            try:
                self.event = json.loads(line)
                # We assume that JSON content follows the format that is produced
                # by the Kaldi-ASR system. This script can be used as a post processing step,
                # for example in 'live' recognition
                # pull apart to process each entry
                for hypo in self.event["result"]["hypotheses"]:
                    line = self.__byteify(hypo["transcript"])
                    line = re.sub(r'(\S)(\.|,)', r'\1 \2', line)
                    self.words.extend(line.strip().split())
                    self.words.append("ENDTRANSCRIPT")
                    if hypo["transcript"]:
                        # sometimes we get empty transcripts and therefore empty alignments.
                        for word in hypo["word-alignment"]:
                            self.words.append(self.__byteify(word["word"]))
                            self.start.append(float(word["start"]))
                            self.duration.append(float(word["length"]))
                            self.pp.append(float(word["confidence"]))
                    self.words.append("ENDHYPO")
            except:
                # plaintext input may have certain punctuation that may interfere with the detection of numbers
                line = re.sub(r'(\S)(\.|,)', r'\1 \2', line)
                self.words = line.strip().split()

    def convertBlock(self, words):

        # Convert a list of words into an integer value.
        # The input list should only contain numeric terms

        value = 0
        nomatch = True

        for i, w in enumerate(number_blocks):
            try:
                index = words.index(number_blocks[i])
                if index == 0:
                    value = 1
                else:
                    value = self.convertBlock(words[0:index])
                rest = self.convertBlock(words[index + 1:])
                value = (value * getallen[w]) + rest
                nomatch = False
                break
            except:
                continue

        if nomatch:
            for w in words:
                value += getallen[w]

        return value

    def convert(self):
        numbers = []
        for w in self.words:
            if (w in dd and len(numbers)>0 and numbers[-1] in dd):
                self.result.append(str(self.convertBlock(numbers)))
                self.offset.append(len(numbers))
                numbers = []
                numbers.append(w)
            elif (w in digits and len(numbers) > 1 and numbers[-1] == 'en' and numbers[-2] in ['honderd', 'duizend']):
                numbers.append(w)
            elif (w in dnb and len(numbers)>1 and numbers[-1]=='en' and numbers[-2] in dnb) or (w=='en' and len(numbers)>0 and numbers[-1] not in dnb):
                self.result.append(str(self.convertBlock(numbers)))
                self.offset.append(len(numbers)-1)
                self.result.append('en')
                self.offset.append(1)
                numbers=[]
                numbers.append(w)
            elif (w=='en' and len(numbers)==0):
                self.result.append('en')
                self.offset.append(1)
            elif w in getallen:
                numbers.append(w)
            else:
                if len(numbers):
                    self.result.append(str(self.convertBlock(numbers)))
                    if numbers[-1]=='en':
                        self.result.append('en')
                        self.offset.append(len(numbers)-1)
                        self.offset.append(1)
                    else: self.offset.append(len(numbers))
                    numbers = []
                self.result.append(w)
                self.offset.append(1)
        if len(numbers):
            self.result.append(str(self.convertBlock(numbers)))
            self.offset.append(len(numbers))

    def handleCommas(self):
        # remove spaces for individual digits after a comma (used as a period in Dutch)
        # and replace the word comma with an actual comma
        i=1
        while i<(len(self.result)-1):
            if self.result[i]=='komma' and re.match(r'\d+', self.result[i-1]) and re.match(r'\d+', self.result[i+1]):
                self.result[i-1]=self.result[i-1] + ',' + self.result[i+1]
                self.offset[i-1]+=1 + self.offset[i+1]
                del self.result[i: i+2]
                del self.offset[i: i+2]
                while len(self.result)>i and re.match(r'^\d$', self.result[i]):
                    # after a comma, add any additional individual digits
                    self.result[i-1]=self.result[i-1] + self.result[1]
                    self.offset[i-1]+=self.offset[i]
                    del self.result[i]
                    del self.offset[i]
            else:
                i+=1

    def handleCombos(self):
        # Typically a combination of two 2-digit terms refers to either a calendar year or part of a Dutch zipcode
        # We combine them if possible, but beware that this may introduce mistakes here and there
        i = 1
        while i < (len(self.result)):
            if re.match(r'^\d{2}$', self.result[i-1]) and re.match(r'^\d{2}$', self.result[i]):
                if (i>1 and re.match(r'^\d{2}$', self.result[i-2])) or (i<(len(self.result)-1) and re.match(r'^\d{2}$', self.result[i+1])):
                    # don't do anything if it's not just two two-digit groups
                    i+=1
                else:
                    self.result[i-1]=self.result[i-1]+self.result[i]
                    self.offset[i-1]+=self.offset[i]
                    del self.result[i]
                    del self.offset[i]
            else:
                i+=1

    def words2num(self):
        self.convert()
        self.handleCommas()
        self.handleCombos()

    def getResult(self):
        output=''

        if self.ident:
            # if the input was a .ctm file, recreate it
            i = 0
            ii = 0
            while i < len(self.result):
                output += "%s %s %.2f %.2f %s" % ( self.ident, self.channel[ii], self.start[ii], sum(self.duration[ii:ii+self.offset[i]]), self.result[i] )
                if len(self.pp):
                    output +=  "%.3f\n" % ( min(self.pp[ii:ii+self.offset[i]]) )
                else:
                    output += "\n"
                ii+=self.offset[i]
                i+=1

        elif self.event:
            # rebuild the json string, be non-destructive
            event = self.event.copy()
            result = self.result[:]
            offset = self.offset[:]
            duration = self.duration[:]
            start = self.start[:]
            pp = self.pp[:]

            i = 0
            hypno = 0
            while len(result):
                wa=0
                # rewrite the transcript part
                while result[0]!="ENDTRANSCRIPT":
                    output += result[0] + ' '
                    del result[0]
                    del offset[0]
                del result[0]
                del offset[0]

                # get rid of the extra space before some punctuation
                output = re.sub(r'\s(\.|,)', r'\1', output)
                event["result"]["hypotheses"][hypno]["transcript"]=output.strip()
                output = ''
                # rewrite the individual words
                while result[0]!="ENDHYPO":
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["word"]=result[0]
                    del result[0]
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["start"]=start[0]
                    del start[:offset[0]]
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["length"]=sum(duration[:offset[0]])
                    del duration[:offset[0]]
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["confidence"] = min(pp[:offset[0]])
                    del pp[:offset[0]]
                    wa += 1
                    del offset[0]
                try:
                    while 1: del event["result"]["hypotheses"][hypno]["word-alignment"][wa]
                except:
                    pass
                del result[0]
                del offset[0]
                hypno+=1
            output = json.dumps(event)

        else:
            # or just output plaintext
            if len(self.result)>0:
                output=' '.join(self.result)
            else:
                output=''
            # get rid of the extra space before some punctuation
            output=re.sub(r'\s(\.|,)', r'\1', output)

        return output

def main():
    while True:
        transcript = Transcript()
        transcript.readInput()
        if transcript.isValid():
            transcript.words2num()
            print transcript.getResult()
            sys.stdout.flush()
        else:
            break

if __name__ == "__main__":
    main()
