#!/bin/bash
MYFULLPATH=`readlink -f $0`
CURDIR=`dirname $MYFULLPATH`

LOCALSCRIPTSDIR=$CURDIR/morph-expand-scripts

. $CURDIR/shflags

. $LOCALSCRIPTSDIR/morph-expand-common.sh

TEMPFIELDSEPARATOR="vmsanchezPROMPSITunlikelyfieldseparator"

function join_first_two_fields {
	sed "s:	:$TEMPFIELDSEPARATOR:"
}

function unjoin_first_two_fields {
	sed "s:$TEMPFIELDSEPARATOR:	:"
}

function phrase_table_to_tab {
	sed -r 's:[ ]?\|\|\|[ ]?:	:g'
}

function tab_to_phrase_table {
	sed 's:	: ||| :g' | sed 's:  : :g' | sed 's:^ ::' | sed 's: $::'
}

function get_tl_lex_counts {
	local ALIGNMENTSFILE=$1
	local TLCORPUSFILE=$2
	local OUTPUTFILE=$3

#we count also unaligned words. See file mosesdecoder-RELEASE-3.0/scripts/training/LexicalTranslationModel.pm
	paste $ALIGNMENTSFILE $TLCORPUSFILE | python -c '
import sys
for line in sys.stdin:
	line=line.rstrip("\n")
	mainparts=line.split("\t")
	alignmentsPairs=mainparts[0].split(" ")
	tokens=mainparts[1].split(" ")
	alignedtlindexes=set()
	for alpair in alignmentsPairs:
		tlindex=int(alpair.split("-")[1])
		alignedtlindexes.add(tlindex)
		print tokens[tlindex]
	for i in range(len(tokens)):
		if i not in alignedtlindexes:
			print tokens[i]
' | LC_ALL=C sort | LC_ALL=C uniq -c | sed 's:^[ ]*::' | sed -r 's:[ ]+:	:' > $OUTPUTFILE

}

function get_sl_lex_counts {
	local ALIGNMENTSFILE=$1
	local SLCORPUSFILE=$2
	local OUTPUTFILE=$3

#we count also unaligned words. See file mosesdecoder-RELEASE-3.0/scripts/training/LexicalTranslationModel.pm
	paste $ALIGNMENTSFILE $SLCORPUSFILE | python -c '
import sys
for line in sys.stdin:
	line=line.rstrip("\n")
	mainparts=line.split("\t")
	alignmentsPairs=mainparts[0].split(" ")
	tokens=mainparts[1].split(" ")
	alignedslindexes=set()
	for alpair in alignmentsPairs:
		tlindex=int(alpair.split("-")[0])
		alignedslindexes.add(tlindex)
		print tokens[tlindex]
	for i in range(len(tokens)):
		if i not in alignedslindexes:
			print tokens[i]
' | LC_ALL=C sort | LC_ALL=C uniq -c | sed 's:^[ ]*::' | sed -r 's:[ ]+:	:' > $OUTPUTFILE

}


DEFINE_string 'source_language' 'en' 'Source language code' 's'
DEFINE_string 'target_language' 'hr' 'Target language code' 't'
DEFINE_string 'phrase_table' '' 'Phrase table file to be expanded' 'p'
DEFINE_string 'new_phrase-table' '' 'Phrase table file that will be generated' 'o'
DEFINE_string 'work_dir' '' 'Directory where all the intermediate steps will be stored' 'w'
DEFINE_string 'tag_groups' '' 'File with tag groups to be expanded in the TL' 'g'
DEFINE_string 'lexicon' '' 'File with the TL lexicon' 'l'
DEFINE_string 'tag_prob_from_corpus' '' 'Include probability of the morp tag in the new phrase table. Use the corpus passed as parameter. IMPORTANT: if you are generating a phrase table with lexicalized factors, use a monolingual corpus WITHOUT lexicalized factors for this option' 'c'
DEFINE_string 'unfactored_phrase_table' '' 'Generate a phrase table based only on surface forms. Use this phrase table to avoid generating existing phrases' 'u'
DEFINE_string 'unlexicalized_corpus' '' 'If you are going to generate a synthetic phrase table with lexicalized factors, use this argument to specify the TL side of a factored, unlexicalized corpus' 'x'
DEFINE_boolean 'use_cond_prob' false 'Use conditional tag probability' 'C'

FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

if [ ${FLAGS_help} == ${FLAGS_TRUE} ] ; then
    exit 0;
fi

SL=${FLAGS_source_language}
TL=${FLAGS_target_language}
WORKDIR=${FLAGS_work_dir}
ORIGINALPHRASETABLE=${FLAGS_phrase_table}
TAGGROUPS=${FLAGS_tag_groups}
LEXICON=${FLAGS_lexicon}
NEWPHRASETABLE=${FLAGS_new_phrase_table}
CORPUSFORTAGPROB=${FLAGS_tag_prob_from_corpus}
UNFACTOREDPHRASETABLE=${FLAGS_unfactored_phrase_table}
UNLEXICALIZEDCORPUS="${FLAGS_unlexicalized_corpus}"

USECONDPROBFLAG=""
if [ "${FLAGS_use_cond_prob}" == "${FLAGS_TRUE}"  ]; then
	USECONDPROBFLAG="--use_cond_prob"
fi

MODELDIR=`dirname $ORIGINALPHRASETABLE`

mkdir -p $WORKDIR

LEXICALIZEDMAPPINGSFLAG=""
#0. If we are expanding a lexicalized phrase table, we will need mappings between tags and their lexicalization
if [ "$UNLEXICALIZEDCORPUS" != "" ]; then
	LEXICALIZEDMAPPINGSFLAG="--lexicalized_mappings $WORKDIR/lexicalizedMappings"
	if [ ! -f "$WORKDIR/lexicalizedMappings" ]; then
		cat "$UNLEXICALIZEDCORPUS" | tr ' ' '\n' | sed 's:|:	:' | grep -v 'Unk' | LC_ALL=C sort -u > "$WORKDIR/lexicalizedMappings"
	fi
fi

#1. Select candidate phrase entries that can be expanded
#They are those whose sequence of TL tags belong to a group
if [ ! -f "$WORKDIR/expandable-phrase-table.tab.gz" ]; then
zcat $ORIGINALPHRASETABLE | phrase_table_to_tab | python $LOCALSCRIPTSDIR/select-expandable-phrases-multi.py --tag_groups $TAGGROUPS $LEXICALIZEDMAPPINGSFLAG  | gzip > $WORKDIR/expandable-phrase-table.tab.gz
fi

#2. Create a phrase table with pseudo-lemmatized expandable entries, and sum their probabilities
#2.1 Extract lexical counts of each TL token. We will need them in order to properly normalise probabilities of new entries
if [ ! -f "$WORKDIR/lexcounts.$TL" ]; then
get_tl_lex_counts $MODELDIR/aligned.grow-diag-final-and $MODELDIR/aligned.0,1.$TL $WORKDIR/lexcounts.$TL
fi

if [ ! -f "$WORKDIR/lexcounts.$SL" ]; then
get_sl_lex_counts $MODELDIR/aligned.grow-diag-final-and $MODELDIR/aligned.0.$SL $WORKDIR/lexcounts.$SL
fi

#2.2 Actually create the phrase table
#pseudo-lemmatize generates 2 different TL collumns:the lemmatized one and the original one afterwards
#sum-probs prints only the lemmatized one, with all the probabilities correctly estimated
if [ ! -f "$WORKDIR/pre-pseudo-lemmatized-phrase-table.tab.gz" ]; then
zcat $WORKDIR/expandable-phrase-table.tab.gz  | python $LOCALSCRIPTSDIR/pseudo-lemmatize-multi.py --tag_groups $TAGGROUPS --lexicon $LEXICON $LEXICALIZEDMAPPINGSFLAG | LC_ALL=C sort -k1,2 -t '	' | gzip > $WORKDIR/pre-pseudo-lemmatized-phrase-table.tab.gz
fi

if [ ! -f "$WORKDIR/pseudo-lemmatized-phrase-table.tab.gz" ]; then
 zcat $WORKDIR/pre-pseudo-lemmatized-phrase-table.tab.gz | python $LOCALSCRIPTSDIR/sum-probs-multi.py --lexcounts $WORKDIR/lexcounts.$TL --lexcountssl $WORKDIR/lexcounts.$SL --lexf2e $MODELDIR/lex.0-0,1.f2e  --lexe2f $MODELDIR/lex.0-0,1.e2f | gzip > $WORKDIR/pseudo-lemmatized-phrase-table.tab.gz
fi

#2.3 Obtain probs of each tag from existing tagged monolingual corpus
if [ "$CORPUSFORTAGPROB" != "" ]; then
	if [ ! -f "$WORKDIR/tagfreqs" ]; then
		compute_tag_freqs "$CORPUSFORTAGPROB" "$WORKDIR/tagfreqs"
	fi

fi

#3. Create the new phrase pairs after expansion and remove those already existing
if [ ! -f  "$NEWPHRASETABLE" ]; then
	if [ "$UNFACTOREDPHRASETABLE" != "" ]; then
		zcat $UNFACTOREDPHRASETABLE | phrase_table_to_tab | python $LOCALSCRIPTSDIR/select-expandable-phrases.py |  join_first_two_fields | LC_ALL=C sort -k1,1 -t '	' > $WORKDIR/unfactored-phrase-table-for-filtering.first2join
		REFERENCEPHRASETABLE=$WORKDIR/unfactored-phrase-table-for-filtering.first2join
	else
		zcat $WORKDIR/expandable-phrase-table.tab.gz | join_first_two_fields | LC_ALL=C sort -k1,1 -t '	' > $WORKDIR/expandable-phrase-table.first2joint
		REFERENCEPHRASETABLE=$WORKDIR/expandable-phrase-table.first2joint
	fi

NUMFIELDS=`zcat $WORKDIR/pseudo-lemmatized-phrase-table.tab.gz | head -n 1 | awk -F"\t" '{print NF}'`
EXPECTEDFIELDS=`expr $NUMFIELDS - 1`
#output of expand-phrases contains 3 columns separated by tab: SL phrase | expanded TL phrase | pseudo-lemmatized TL phrase
#join + awk command makes sure that only phrases not existing in the original phrase table are generated

JOINENTRIESSAMESURFACEFLAG=""
if [ "$UNFACTOREDPHRASETABLE" != "" ]; then
	JOINENTRIESSAMESURFACEFLAG="--join_same_surface"
fi
zcat $WORKDIR/pseudo-lemmatized-phrase-table.tab.gz | {
if [ "$CORPUSFORTAGPROB" != "" ]; then
	python $LOCALSCRIPTSDIR/expand-phrases-with-tagprob-multi.py --lexicon $LEXICON  --tag_freqs "$WORKDIR/tagfreqs" --tag_groups $TAGGROUPS $JOINENTRIESSAMESURFACEFLAG $USECONDPROBFLAG
else
	python $LOCALSCRIPTSDIR/expand-phrases.py --lexicon $LEXICON $JOINENTRIESSAMESURFACEFLAG
fi
}|  {
#If we are generating a surface-form based phrase table, we must again sum probs of equal phrases
if [ "$UNFACTOREDPHRASETABLE" != "" ]; then
	cat - |  LC_ALL=C sort -k1,2 -t '	' | python $LOCALSCRIPTSDIR/sum-probs.py
else
	cat -
fi
} | {
if [ "$UNLEXICALIZEDCORPUS" != "" ]; then
	#we re-lexicalize the generated phrase pairs
	cat - | python $LOCALSCRIPTSDIR/lexicalizeFactors.py --closed_adverbs $LOCALSCRIPTSDIR/closed-adverbs --field 1
else
	cat -
fi

}  | join_first_two_fields  | LC_ALL=C sort -k1,1 -u -t '	'  | LC_ALL=C join -1 1 -2 1 -a 1 -t '	' - $REFERENCEPHRASETABLE | awk -vexpected=$EXPECTEDFIELDS -F"\t" '{ if(NF == expected){ print $0 } }' | unjoin_first_two_fields | tab_to_phrase_table | LC_ALL=C sort | gzip > "$WORKDIR/newphrasetable.debug.gz"

zcat "$WORKDIR/newphrasetable.debug.gz" | python -c '
import sys
for line in sys.stdin:
	line=line.rstrip("\n")
	parts=line.split("|||")
	parts[-1]=""
	print "|||".join(parts)
' | gzip > $NEWPHRASETABLE
rm -f $WORKDIR/expandable-phrase-table.first2joint
fi
