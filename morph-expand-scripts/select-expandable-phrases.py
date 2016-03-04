import sys,codecs, argparse
from morphExpansionUtils import TagGroups

ENCODING="utf-8"

#If tag_groups parameter is not set, it does not check morph tags
parser=argparse.ArgumentParser(description="print only phrase pairs that can be expanded")
parser.add_argument("--tag_groups")
args = parser.parse_args()

#Load tag groups
if args.tag_groups:
	tagGroups=TagGroups(codecs.open(args.tag_groups,'r',ENCODING))
else:
	tagGroups=None

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split("\t")
	sltokens=parts[0].split()
	tltokens=parts[1].split()
	if len(sltokens) == 1 and len(tltokens) == 1:
		if tagGroups != None:
			morphTag=tltokens[0].split(u"|")[1]
			tagGroup=tagGroups.getGroup(morphTag)
			if tagGroup != None:
				print line.encode(ENCODING)
		else:
			print line.encode(ENCODING)
