import sys,codecs, argparse
from morphExpansionUtils import TagGroupsMulti

ENCODING="utf-8"

#If tag_groups parameter is not set, it does not check morph tags
parser=argparse.ArgumentParser(description="print only phrase pairs that can be expanded")
parser.add_argument("--tag_groups")
parser.add_argument("--lexicalized_mappings")
args = parser.parse_args()

#Load tag groups
if args.tag_groups:
	tagGroups=TagGroupsMulti(codecs.open(args.tag_groups,'r',ENCODING))
else:
	tagGroups=None

if args.lexicalized_mappings:
	tagGroups.addLexicalizedMappings(codecs.open(args.lexicalized_mappings,'r',ENCODING))

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split("\t")
	sltokens=parts[0].split()
	tltokens=parts[1].split()
	if tagGroups != None:
		morphTag=[tltoken.split(u"|")[1] for tltoken in tltokens]
		words=[tltoken.split(u"|")[0] for tltoken in tltokens]
		tagGroup,detectedTagSequence=tagGroups.getGroupWithLexUnits(morphTag,words)
		if tagGroup != None:
			print line.encode(ENCODING)
	else:
		print line.encode(ENCODING)
