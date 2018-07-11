# Words2Num_nl

The main job of this script is to convert a textual input containing spelled out numbers into one where numeric values are written as numbers. It is suitable only for **DUTCH**. Spelled out numbers are expected to be deconstructed in a way that is typically found in automatic speech recognition, e.g., `twee en twintig`, `honderd veertien`.

Input can be plaintext, [.ctm file format](http://www1.icsi.berkeley.edu/Speech/docs/sctk-1.2/infmts.htm), or JSON strings in a format that is compatible with Kaldi's output. This script could for example be included in a full postprocessor pipeline for [a Kaldi-based live recognition system](https://github.com/alumae/kaldi-gstreamer-server).

Usage:\
`echo 'Op vier juli twee duizend achttien was het mooi weer in postcodegebied vijf en zestig drie en veertig' | ./words2num_nl.py`

Results in:\
`Op 4 juli 2018 was het mooi weer in postcodegebied 6543`

Some special cases are recognized, such as pairs of two-digit numbers which can be combined into one four-digit number as these often refer to either calender years or zip-codes in Dutch. Also the word 'komma' between numbers is interpreted as a decimal symbol.
