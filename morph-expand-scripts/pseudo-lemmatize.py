import sys,codecs, gzip, argparse
from morphExpansionUtils import TagGroups,Lexicon
ENCODING="utf-8"

parser=argparse.ArgumentParser(description="replace inflected forms with lemmas and set of possible tags")
parser.add_argument("--tag_groups")
parser.add_argument("--lexicon")
args = parser.parse_args()

tagGroups=TagGroups(codecs.open(args.tag_groups,'r',ENCODING))

myreader=codecs.getreader(ENCODING)
lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')))

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split("\t")
	#parts[1] is TL side of phrase table
	tltokens=parts[1].split(" ")
	#we will only modify first token
	firsttokenparts=tltokens[0].split(u"|")
	surface=firsttokenparts[0]
	morphTag=firsttokenparts[1]
	tagGroup=tagGroups.getGroup(morphTag)
	if tagGroup != None:
		tagGroupStr=TagGroups.groupToString(tagGroup)
		lemma=lexicon.getLemma(surface,morphTag)
		if lemma != None:
			tltokens[0]=lemma+u"|"+tagGroupStr
			newtl=u" ".join(tltokens)
			print u"\t".join([parts[0],newtl,parts[1]]+parts[2:]).encode(ENCODING)
