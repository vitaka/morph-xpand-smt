#! /bin/bash

#Filter synthetic phrase table and keep only some phrases

function do_filter {
local SLLENGTH="$1"
local TLPOS="$2"

python -c '
import sys
sllenStr=sys.argv[1]
if len(sllenStr) > 0:
	sllenFilter=int(sllenStr)
else:
	sllenFilter=None
tlPosFilter_s=set(sys.argv[2].split(","))
for line in sys.stdin:
	line=line.rstrip("\n")
	parts=line.split(" ||| ")
	numSlTokens=len(parts[0].strip().split(" "))
	slCondition=True
	if sllenFilter != None and numSlTokens != sllenFilter:
		slCondition=False
	tlCondition=True
	tlPos_l=[]
	tltokens=parts[1].split(" ")
	for token in tltokens:
		tlPos_l.append(token.split("|")[1][:1])
	tlPos="".join(tlPos_l)
	if tlPos not in tlPosFilter_s:
		tlCondition=False
	if slCondition and tlCondition:
		print line
' "$SLLENGTH" "$TLPOS"

}

INPUTPT="$1"
INPUTNOGZ="${INPUTPT%.gz}"

#for CONFIG in "-N" "1-N" "-A" "1-A" "-AN" "-AAN" "-NN" "-NCN" "1-V" "-V" "-VN" "-RV"  "-PV" "-VP" "1-VV" "-VV" ; do
#	NUMFILTER=`echo "$CONFIG" | cut -f 1 -d '-'`
#	POSFILTER=`echo "$CONFIG" | cut -f 2 -d '-'`
#	zcat $INPUTPT | do_filter "$NUMFILTER" "$POSFILTER" | gzip > $INPUTNOGZ.$CONFIG.gz
#
#done

zcat $INPUTPT | do_filter "" "N,AN,AAN,NN,NCN,VN" | gzip > "$INPUTNOGZ.-N,-AN,-AAN,-NN,-NCN,-VN.gz"
