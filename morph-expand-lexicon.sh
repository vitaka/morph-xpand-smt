#!/bin/bash
MYFULLPATH=`readlink -f $0`
CURDIR=`dirname $MYFULLPATH`

LOCALSCRIPTSDIR=$CURDIR/morph-expand-scripts

. $LOCALSCRIPTSDIR/morph-expand-common.sh

function remove_entities {

sed 's:&quot;:":g' | sed 's:&amp;:\&:g'| sed 's:&lt;:<:g' | sed 's:&gt;:>:g' | sed "s:&apos;:':g"

}


. $CURDIR/shflags

DEFINE_string 'source_language' 'en' 'Source language code' 's'
DEFINE_string 'target_language' 'hr' 'Target language code' 't'
DEFINE_string 'bil_lexicon' '' 'Bilingual lexicon to be expanded' 'i'
DEFINE_string 'new_phrase-table' '' 'Phrase table file that will be generated' 'o'
DEFINE_string 'work_dir' '' 'Directory where all the intermediate steps will be stored' 'w'
DEFINE_string 'tag_groups' '' 'File with tag groups to be expanded in the TL' 'g'
DEFINE_string 'lexicon' '' 'File with the TL lexicon' 'l'
DEFINE_string 'lexicon_sl' '' 'File with the SL lexicon' 'L'
DEFINE_string 'tag_prob_from_corpus' '' 'Include probability of the morp tag in the new phrase table. Use the corpus passed as parameter. IMPORTANT: if you are generating a phrase table with lexicalized factors, use a monolingual corpus WITHOUT lexicalized factors for this option' 'c'
DEFINE_string 'moses_dir' '' 'Moses installation directory' 'm'
DEFINE_boolean 'expand_sl' false 'Expand also SL side of the lexicon' 'e'
DEFINE_boolean 'remove_adj' false 'Dont generate neither expand adjectives in Croatian' 'a'
DEFINE_string 'original_training_dir' '' 'With this method, a single phrase table that combines original one and lexicon-derived one is created' 'M'

FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

if [ ${FLAGS_help} == ${FLAGS_TRUE} ] ; then
    exit 0;
fi


SL=${FLAGS_source_language}
TL=${FLAGS_target_language}
WORKDIR=${FLAGS_work_dir}
INPUTLEXICON=${FLAGS_bil_lexicon}
TAGGROUPS=${FLAGS_tag_groups}
LEXICON=${FLAGS_lexicon}
LEXICONSL=${FLAGS_lexicon_sl}
NEWPHRASETABLE=${FLAGS_new_phrase_table}
CORPUSFORTAGPROB=${FLAGS_tag_prob_from_corpus}
MOSESDIR="${FLAGS_moses_dir}"
ORIGINALTRAININGDIR="${FLAGS_original_training_dir}"

EXPANDSLFLAG=""
if [ "${FLAGS_expand_sl}" == "${FLAGS_TRUE}" ]; then
	EXPANDSLFLAG="--expand_sl"
fi

REMOVEADJFLAG=""
if [ "${FLAGS_remove_adj}" == "${FLAGS_TRUE}" ]; then
	REMOVEADJFLAG="--remove_adj"
fi

TOKENIZER="$MOSESDIR/scripts/tokenizer/tokenizer.perl"
ESCAPER="$MOSESDIR/scripts/tokenizer/escape-special-chars.perl"
REMENT=

mkdir -p $WORKDIR

#1. fix encoding of lexicon and tokenize
tr -d '\r'  < $INPUTLEXICON  | iconv -f WINDOWS-1250 -t utf-8 > $WORKDIR/bilLexicon

cut -f 1 $WORKDIR/bilLexicon | $TOKENIZER -l $SL > $WORKDIR/bilLexicon.tok.$SL
cut -f 2 $WORKDIR/bilLexicon | $TOKENIZER -l $TL > $WORKDIR/bilLexicon.tok.$TL
cat $WORKDIR/bilLexicon.tok.$TL  | remove_entities > $WORKDIR/bilLexicon.tok.remEnt.$TL
cat $WORKDIR/bilLexicon.tok.$SL  | remove_entities > $WORKDIR/bilLexicon.tok.remEnt.$SL

paste $WORKDIR/bilLexicon.tok.remEnt.$SL $WORKDIR/bilLexicon.tok.remEnt.$TL > $WORKDIR/bilLexicon.tok.remEnt


#2. expand entries and add factors,
# Alorithm is as follows:
# if TL contais more than one word:
#   use tagger,
# else:
#   if TL is a lemma:
#      expand according to tag groups
#   else:
#      do not expand, just add factor from lexicon
#
if [ ! -f "$WORKDIR/bilFactoredLexicon" ]; then

awk -F'\t' '{ split($2,array," "); if (length(array) == 1) { print $0 } }' < $WORKDIR/bilLexicon.tok.remEnt > $WORKDIR/bilLexiconMonoTL
awk -F'\t' '{ split($2,array," "); if (length(array) > 1) { print $0 } }' < $WORKDIR/bilLexicon.tok.remEnt > $WORKDIR/bilLexiconMultiTL


python $LOCALSCRIPTSDIR/expand-bilingual-lexicon.py --lexicon $LEXICON --lexicon_sl $LEXICONSL $EXPANDSLFLAG $REMOVEADJFLAG < $WORKDIR/bilLexiconMonoTL > $WORKDIR/bilFactoredLexiconMonoTL


awk -F'\t' '{ print $2; }' < $WORKDIR/bilLexiconMultiTL | python $LOCALSCRIPTSDIR/crf-tagger-with-lexicon.py  > $WORKDIR/bilLexiconMultiTL.onlyfactors
awk -F'\t' '{ print $1; }' < $WORKDIR/bilLexiconMultiTL > $WORKDIR/bilLexiconMultiTL.onlySL

awk -F'\t' '{ print $2; }' < $WORKDIR/bilLexiconMultiTL | paste - $WORKDIR/bilLexiconMultiTL.onlyfactors | python $LOCALSCRIPTSDIR/joinCorpusAndfactors.py | paste $WORKDIR/bilLexiconMultiTL.onlySL - > $WORKDIR/bilFactoredLexiconMultiTL

cat $WORKDIR/bilFactoredLexiconMonoTL $WORKDIR/bilFactoredLexiconMultiTL > $WORKDIR/bilFactoredLexicon.preesc

#Re-tokenize (in order to cancel the effect of remove_entities) and escape special chars
cut -f 2 $WORKDIR/bilFactoredLexicon.preesc | python -c '
import sys
for line in sys.stdin:
	print " ".join([ tok.split("|")[1] for tok in line.rstrip("\n").split(" ") ])
' > $WORKDIR/bilFactoredLexicon.preesc.factors

cut -f 2 $WORKDIR/bilFactoredLexicon.preesc | python -c '
import sys
for line in sys.stdin:
	print " ".join([ tok.split("|")[0] for tok in line.rstrip("\n").split(" ") ])
' | $TOKENIZER -l $TL | $ESCAPER > $WORKDIR/bilFactoredLexicon.preesc.escapedwords

cut -f 1 $WORKDIR/bilFactoredLexicon.preesc | $TOKENIZER -l $SL | $ESCAPER | paste - $WORKDIR/bilFactoredLexicon.preesc.escapedwords $WORKDIR/bilFactoredLexicon.preesc.factors | python -c '
import sys
for line in sys.stdin:
	line=line.rstrip("\n")
	parts=line.split("\t")
	tlwords=parts[1].split(" ")
	tltags=parts[2].split(" ")
	newtlpart=" ".join([ w+"|"+tag for w,tag in zip(tlwords,tltags) ])
	print parts[0]+"\t"+newtlpart

' | LC_ALL=C sort -u > $WORKDIR/bilFactoredLexicon

fi

#3. Learn lexical translation model
if [ ! -f "$WORKDIR/train-lex-model/model/aligned.grow-diag-final-and" ]; then
mkdir -p $WORKDIR/train-lex-model/corpus
cut -f 1 $WORKDIR/bilFactoredLexicon > $WORKDIR/train-lex-model/corpus/corpus.$SL
cut -f 2 $WORKDIR/bilFactoredLexicon > $WORKDIR/train-lex-model/corpus/corpus.$TL

$MOSESDIR/scripts/training/train-model.perl --root-dir $WORKDIR/train-lex-model --corpus $WORKDIR/train-lex-model/corpus/corpus --f $SL --e $TL --translation-factors 0-0,1 --parallel --alignment grow-diag-final-and --external-bin-dir $MOSESDIR/../moses-training-tools --mgiza --mgiza-cpus 8 --last-step 4

fi

#4. generate extract.* files
if [ ! -f "$WORKDIR/train-full-model/model/extract.0-0,1.inv.sorted.gz" ]; then
mkdir -p $WORKDIR/train-full-model/model
paste $WORKDIR/bilFactoredLexicon $WORKDIR/train-lex-model/model/aligned.grow-diag-final-and | sed 's:	: ||| :g' | LC_ALL=C sort | gzip > $WORKDIR/train-full-model/model/extract.0-0,1.sorted.gz
cat $WORKDIR/train-lex-model/model/aligned.grow-diag-final-and | python -c '
import sys
for line in sys.stdin:
	line=line.rstrip("\n")
	pairs=line.split(" ")
	splitPairs=[ pair.split("-") for pair in pairs ]
	print " ".join( sp[1]+"-"+sp[0] for sp in splitPairs )
' > $WORKDIR/train-lex-model/model/aligned.grow-diag-final-and.reversed
paste $WORKDIR/bilFactoredLexicon $WORKDIR/train-lex-model/model/aligned.grow-diag-final-and.reversed | awk -F'\t' '{ print $2 "\t" $1 "\t" $3 }' | sed 's:	: ||| :g' | LC_ALL=C sort | gzip > $WORKDIR/train-full-model/model/extract.0-0,1.inv.sorted.gz
fi

if [ "$ORIGINALTRAININGDIR" == "" ]; then

	#6. Create phrase table
	if [ ! -f "$WORKDIR/train-full-model/model/phrase-table.0-0,1.gz" ]; then
	cp $WORKDIR/train-lex-model/model/lex.* $WORKDIR/train-full-model/model/
	$MOSESDIR/scripts/training/train-model.perl --root-dir $WORKDIR/train-full-model --f $SL --e $TL --translation-factors 0-0,1 --parallel --alignment grow-diag-final-and --external-bin-dir $MOSESDIR/../moses-training-tools --mgiza --mgiza-cpus 8 --first-step 6 --last-step 6
	fi

	#7. re-normalize probabilities according to frequency in corpus
	if [ "$CORPUSFORTAGPROB" != "" ]; then
		if [ ! -f "$WORKDIR/tagfreqs" ]; then
			compute_tag_freqs "$CORPUSFORTAGPROB" "$WORKDIR/tagfreqs"
		fi

		zcat $WORKDIR/train-full-model/model/phrase-table.0-0,1.gz | python $LOCALSCRIPTSDIR/apply-tag-freqs-to-lexicon.py --lexicon $LEXICON --tag_freqs "$WORKDIR/tagfreqs" | LC_ALL=C sort | gzip > $NEWPHRASETABLE

	else
		cat $WORKDIR/train-full-model/model/phrase-table.0-0,1.gz > $NEWPHRASETABLE
	fi
else

	#train lexical translation model from concatenation of original + expanded parallel corpora
	if [ ! -f "$WORKDIR/train-joint-lex-model/model/lex.0-0,1.e2f" ]; then
		mkdir -p $WORKDIR/train-joint-lex-model/corpus
		mkdir -p $WORKDIR/train-joint-lex-model/model
		for MYLANG in  $SL $TL ; do
			cat $ORIGINALTRAININGDIR/corpus/corpus.$MYLANG $WORKDIR/train-lex-model/corpus/corpus.$MYLANG > $WORKDIR/train-joint-lex-model/corpus/corpus.$MYLANG
		done
		cat $ORIGINALTRAININGDIR/model/aligned.grow-diag-final-and  $WORKDIR/train-lex-model/model/aligned.grow-diag-final-and > $WORKDIR/train-joint-lex-model/model/aligned.grow-diag-final-and
		$MOSESDIR/scripts/training/train-model.perl --root-dir $WORKDIR/train-joint-lex-model --corpus $WORKDIR/train-joint-lex-model/corpus/corpus --f $SL --e $TL --translation-factors 0-0,1 --parallel --alignment grow-diag-final-and --external-bin-dir $MOSESDIR/../moses-training-tools --mgiza --mgiza-cpus 8 --first-step 4 --last-step 4
	fi

	#build phrase table from concatenation of lexicon and original
	if [ ! -f "$WORKDIR/train-joint-full-model/model/phrase-table.0-0,1.gz" ]; then
		mkdir -p  $WORKDIR/train-joint-full-model/model
		ln -s  ../../train-joint-lex-model/model/lex.0-0,1.e2f $WORKDIR/train-joint-full-model/model/lex.0-0,1.e2f
		ln -s  ../../train-joint-lex-model/model/lex.0-0,1.f2e $WORKDIR/train-joint-full-model/model/lex.0-0,1.f2e
		zcat $ORIGINALTRAININGDIR/model/extract.0-0,1.sorted.gz $WORKDIR/train-full-model/model/extract.0-0,1.sorted.gz | LC_ALL=C sort | gzip > $WORKDIR/train-joint-full-model/model/extract.0-0,1.sorted.gz
		zcat $ORIGINALTRAININGDIR/model/extract.0-0,1.inv.sorted.gz $WORKDIR/train-full-model/model/extract.0-0,1.inv.sorted.gz | LC_ALL=C sort | gzip > $WORKDIR/train-joint-full-model/model/extract.0-0,1.inv.sorted.gz
		$MOSESDIR/scripts/training/train-model.perl --root-dir $WORKDIR/train-joint-full-model --f $SL --e $TL --translation-factors 0-0,1 --parallel --alignment grow-diag-final-and --external-bin-dir $MOSESDIR/../moses-training-tools --mgiza --mgiza-cpus 8 --first-step 6 --last-step 6
	fi

	#add new feature function and print to output
	python $LOCALSCRIPTSDIR/addEBMTFeature.py  $WORKDIR/train-full-model/model/extract.0-0,1.sorted.gz $WORKDIR/train-joint-full-model/model/phrase-table.0-0,1.gz | gzip > $NEWPHRASETABLE

fi
