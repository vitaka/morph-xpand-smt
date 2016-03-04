import sys,codecs, gzip, argparse
from morphExpansionUtils import TagGroupsMulti,Lexicon
ENCODING="utf-8"

parser=argparse.ArgumentParser(description="replace inflected forms with lemmas and set of possible tags")
parser.add_argument("--tag_groups")
parser.add_argument("--lexicon")
parser.add_argument("--lexicalized_mappings")
args = parser.parse_args()

tagGroups=TagGroupsMulti(codecs.open(args.tag_groups,'r',ENCODING))
if args.lexicalized_mappings:
	tagGroups.addLexicalizedMappings(codecs.open(args.lexicalized_mappings,'r',ENCODING))

myreader=codecs.getreader(ENCODING)
lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')))

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split("\t")
	#parts[1] is TL side of phrase table
	tltokens=parts[1].split(" ")

	tltokensSplit=[tltoken.split("|") for tltoken in tltokens]
	surface_l=[ tltoken[0] for tltoken in tltokensSplit ]
	morphTag_l=[ tltoken[1] for tltoken in tltokensSplit ]
	tagGroup,detectedTagSequence=tagGroups.getGroupWithLexUnits(morphTag_l,surface_l)
	if tagGroup != None:
		tagGroupStrList=TagGroupsMulti.groupToStringList(tagGroup)
		lemma_l=[lexicon.getLemma(tltokensSplit[i][0],detectedTagSequence[i]) for i in xrange(len(tltokensSplit))]
		if all(lemma != None for lemma in lemma_l):
			for i in range(len(tltokens)):
				tltokens[i]=lemma_l[i]+u"|"+tagGroupStrList[i]
			newtl=u" ".join(tltokens)
			print u"\t".join([parts[0],newtl,parts[1]]+parts[2:]).encode(ENCODING)
