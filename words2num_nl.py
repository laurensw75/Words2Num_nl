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

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def convert_block(words):

    # Convert a list of words into an integer value.
    # The input list should only contain numeric terms

    value=0
    nomatch=True

    for i, w in enumerate(number_blocks):
        try:
            index=words.index(number_blocks[i])
            if index==0:
                value=1
            else:
                value=convert_block(words[0:index])
            rest=convert_block(words[index+1:])
            value=(value*getallen[w])+rest
            nomatch=False
            break
        except:
            continue

    if nomatch:
        for w in words:
            value+=getallen[w]

    return value

def main():
    looked=False
    while 1:
        ident = ''
        event = ''
        channel = []
        start = []
        duration = []
        words = []
        pp = []
        numbers = []
        result = []
        offset = []

        if not looked:
            line=sys.stdin.readline()
        else:
            looked=False
        if not line: break

        # This script can handle various input formats: .ctm, plaintext, or a JSON string as produced by the Kaldi
        # live recognition setup.

        while re.match(r'^(\S+)\s+\S+\s+[0-9.]+\s+[0-9.]+\s+\S+(\s+[0-9.]+)?$',line):
            # For a CTM file read all lines for a file descriptor (column 1)
            parts=line.strip().split()
            if (not ident) or (parts[0]==ident):
                # treat the ctm as a single line for each identifier string
                ident=parts[0]
                channel.append(parts[1])
                start.append(float(parts[2]))
                duration.append(float(parts[3]))
                words.append(parts[4])
                if len(parts)>5: pp.append(float(parts[5]))
                line=sys.stdin.readline()
                if not line: break
            else:
                # new identifier
                looked=True
                break
        if not ident:
            # file is either JSON or plaintext
            try:
                event=json.loads(line)
                # Obviously there could be many different types of json content
                # we can only handle the type that is produced by the Kaldi-ASR system
                # this way you can use this script as a full post processor, for
                # example in live recognition

                # pull apart to process each entry
                for hypo in event["result"]["hypotheses"]:
                    line = byteify(hypo["transcript"])
                    line = re.sub(r'(\S)(\.|,)', r'\1 \2', line)
                    words.extend(line.strip().split())
                    words.append("ENDTRANSCRIPT")
                    if hypo["transcript"]:
                        # sometimes we get empty transcripts and therefore empty alignments.
                        for word in hypo["word-alignment"]:
                            words.append(byteify(word["word"]))
                            start.append(float(word["start"]))
                            duration.append(float(word["length"]))
                            pp.append(float(word["confidence"]))
                    words.append("ENDHYPO")
            except:
                # plaintext input may have certain punctuation that may interfere with the detection of numbers
                if line.strip() == "":
                    print
                    sys.stdout.flush()
                    continue
                line=re.sub(r'(\S)(\.|,)', r'\1 \2', line)
                words=line.strip().split()

        # Interpret lines so that numeric parts are converted and the rest is passed along untouched.
        # A particular challenge is the word 'en' (and) which can occur both as part of a number or
        # as a very common non-numeric word. In certain cases this leads to ambiguous sentences.
        # We cannot disambiguate those automatically within the scope of this script.

        for w in words:
            if (w in dd and len(numbers)>0 and numbers[-1] in dd):
                result.append(str(convert_block(numbers)))
                offset.append(len(numbers))
                numbers = []
                numbers.append(w)
            elif (w in digits and len(numbers) > 1 and numbers[-1] == 'en' and numbers[-2] in ['honderd', 'duizend']):
                numbers.append(w)
            elif (w in dnb and len(numbers)>1 and numbers[-1]=='en' and numbers[-2] in dnb) or (w=='en' and len(numbers)>0 and numbers[-1] not in dnb):
                result.append(str(convert_block(numbers)))
                offset.append(len(numbers)-1)
                result.append('en')
                offset.append(1)
                numbers=[]
                numbers.append(w)
            elif (w=='en' and len(numbers)==0):
                result.append('en')
                offset.append(1)
            elif w in getallen:
                numbers.append(w)
            else:
                if len(numbers):
                    result.append(str(convert_block(numbers)))
                    if numbers[-1]=='en':
                        result.append('en')
                        offset.append(len(numbers)-1)
                        offset.append(1)
                    else: offset.append(len(numbers))
                    numbers = []
                result.append(w)
                offset.append(1)
        if len(numbers):
            result.append(str(convert_block(numbers)))
            offset.append(len(numbers))

        # print converted
        # result=' '.join(final_string)

        # remove spaces for individual digits after a comma (used as a period in Dutch)
        # and replace the word comma with an actual comma
        i=1
        while i<(len(result)-1):
            if result[i]=='komma' and re.match(r'\d+', result[i-1]) and re.match(r'\d+', result[i+1]):
                result[i-1]=result[i-1] + ',' + result[i+1]
                offset[i-1]+=1 + offset[i+1]
                del result[i: i+2]
                del offset[i: i+2]
                while len(result)>i and re.match(r'^\d$', result[i]):
                    # after a comma, add any additional individual digits
                    result[i-1]=result[i-1] + result[1]
                    offset[i-1]+=offset[i]
                    del result[i]
                    del offset[i]
            else:
                i+=1

        # Typically a combination of two 2-digit terms refers to either a calendar year or part of a Dutch zipcode
        # We combine them if possible, but beware that this may introduce mistakes here and there
        i = 1
        while i < (len(result)):
            if re.match(r'^\d{2}$', result[i-1]) and re.match(r'^\d{2}$', result[i]):
                if (i>1 and re.match(r'^\d{2}$', result[i-2])) or (i<(len(result)-1) and re.match(r'^\d{2}$', result[i+1])):
                    # don't do anything if it's not just two two-digit groups
                    i+=1
                else:
                    result[i-1]=result[i-1]+result[i]
                    offset[i-1]+=offset[i]
                    del result[i]
                    del offset[i]
            else:
                i+=1

        if ident:
            # if the input was a .ctm file, recreate it
            i=0
            ii=0
            while i<(len(result)):
                print ident + ' ' + channel[ii] + ' ' + "{:.2f}".format(start[ii]) + ' ' + "{:.2f}".format(sum(duration[ii:ii+offset[i]])) + ' ' + result[i],
                if len(pp):
                    print "{:.3f}".format(min(pp[ii:ii+offset[i]]))
                else:
                    print
                ii+=offset[i]
                i+=1
        elif event:
            # rebuild the json string
            i=0
            hypno=0
            line=""
            while len(result):
                wa=0
                # first rewrite the transcript part
                while result[0]!="ENDTRANSCRIPT":
                    line+=result[0]+' '
                    del result[0]
                    del offset[0]
                del result[0]
                del offset[0]
                # get rid of the extra space before some punctuation
                line = re.sub(r'\s(\.|,)', r'\1', line)
                event["result"]["hypotheses"][hypno]["transcript"]=line.strip()
                line=""
                # second rewrite the individual words
                while result[0]!="ENDHYPO":
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["word"]=result[0]
                    del result[0]
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["start"]=start[0]
                    del start[:offset[0]]
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["length"]=sum(duration[:offset[0]])
                    del duration[:offset[0]]
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["confidence"] = min(pp[:offset[0]])
                    del pp[:offset[0]]
                    wa+=1
                    del offset[0]
                try:
                    while 1: del event["result"]["hypotheses"][hypno]["word-alignment"][wa]
                except:
                    pass
                del result[0]
                del offset[0]
                hypno+=1
            print json.dumps(event)
            sys.stdout.flush()
        else:
            # or just output plaintext
            result=' '.join(result)
            # get rid of the extra space before some punctuation
            result=re.sub(r'\s(\.|,)', r'\1', result)
            print result

if __name__ == "__main__":
    main()