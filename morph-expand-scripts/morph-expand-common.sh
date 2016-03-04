function compute_tag_freqs {
	local TAGGEDCORPUS=$1
	local OUTPUTFILE=$2

	{ if  [[ $TAGGEDCORPUS == *.gz ]]; then
		zcat $TAGGEDCORPUS
	 else
	   	cat $TAGGEDCORPUS
	fi } | python -c '
import sys
MAXN=3
for line in sys.stdin:
	line=line.rstrip("\n")
	fulltokens=line.split(" ")
	tags=[ t.split("|")[1] for t in fulltokens ]
	for i in range(len(tags)):
		for presize in range(MAXN):
			size=presize+1
			if i+size <= len(tags):
				print "__".join(tags[i:i+size])

' | LC_ALL=C sort | LC_ALL=C uniq -c | sed 's:^[ ]*::' | sed 's: :	:' > $OUTPUTFILE
}
