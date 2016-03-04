# English to Croatian SMT enriched with linguistic information

This piece of software implements different strategies followed in order to create a linguistically-enriched English-Croatian SMT system.

## Factored translation model

The first strategy followed was using factored translation models to translate from surface forms to surface form + morphosyntactic factor, and use
an additional language model that operates on the the additional morphosyntactic factor.

In order to use the factored models, we need to tag the SL side of the parallel corpus and the TL monolingual corpus. We noticed a huge improvement
in BLEU score by constraining the tagging to the lexicon and using the special *Unk* factor for words not present in the lexicon. Size of TL vocabulary
is reduced from 1.1M to 0.9M by applying these constraints.

In order to tag a corpus with these restriction, use the program `morph-expand-scripts/crf-tagger-with-lexicon.py`. It reads a tokenized
text from standard input, tags it with a crf tagger, replaces the tag of words not present in the lexicon with an *Unk* tag and
re-tags the words with tags not present in the lexicon with the help of 3-gram language model of morphosyntactic tags.
The output (in stdout) contains only the tags.
Check the files
`/home/vmsanchez/zagreb-2016/morphological-expansion/re-tagging/ngram-model-for-constraining/getTrainingCorpus.sh` and `/home/vmsanchez/zagreb-2016/morphological-expansion/re-tagging/ngram-model-for-constraining/trainLM.sh` at our server for more information about the training of this 3-gram language model.

Since the output of `morph-expand-scripts/crf-tagger-with-lexicon.py` contains only the tags, we need to join them with the surface forms
in order to build the factored parallel corpus. Use the program `morph-expand-scripts/joinCorpusAndfactors.py`. It expects a sequence of surface forms and
the corresponding tags in the same line. A tab character must delimit both sequences. Just call the program with:
```
paste taggingInput taggingOutput | python morph-expand-scripts/joinCorpusAndfactors.py > result
```
This step must be executed even when you do not plan to use the tags in the TL side of a parallel corpus for training factored models
because it fixes some incorrect tagging of numbers done by the previous step.

Once the corpora has been retagged, the target language tag model needs to be re-estimated. Just use the common kenLM parameters (see an example at `/home/vmsanchez/zagreb-2016/morphological-expansion/train-factored-lm-retagged.sh`)

Finally, you can start training the model. File `Makefile-trainmoses` can be helpful. If you want to train the model with the default parameters,
use the script `/home/vmsanchez/zagreb-2016/morphological-expansion/run-experiment-baseline-factored-retagged-order3-multiref.sh` at our server.


## Morphological expansion

Translation quality achieved by the factored system can be further improved by morphologically expanding entries in the phrase table.
In other words, by creating new entries from the existing ones by means of changing values of morphological inflection attributes.

Expansion works with linguistically motivated tag groups. A tag group is a set of tags or sequences of tags. When a phrase pair whose
TL side matches an element of a tag group is identified in the original phrase table, a new phrase pair is generated for each
of the remaining elements of the group. Consider, for instance, the following group for feminine singular nouns:
```
Ncfsn Ncfsa Ncfsi
```
If the following phrase is observed in the original phrase table:
```
house ||| kuća|Ncfsn |||
```
The following new entries are generated:
```
house ||| kuće|Ncfsg |||
house ||| kućicom|Ncfsi |||
```
Concerning probabilities of the new phrase pairs, they are computed as follows:

1. All the phrases in the original phrase table with the same SL side and TL sides belonging to the same tag group are joined together (assuming the frequency of the resulting phrase pair is the sum of the frequencies of the phrase pairs being joined and recomputing all the probabilities).
2. The direct translation probabilities of the generated phrases are multiplied by the relative frequency of the corresponding tag when compare to
the sum of the tags in the tag group.

In order to generate a new phrase table with the morphologically expanded entries, run the program `morph-expand-scripts/morph-expand-phrase-table-multiword.sh`. Here
follows an example of the command run in order to generate a phrase table from the *somecases* tag groups:
```
 bash /home/vmsanchez/software/abumatran-repo/morph-expand-phrase-table-multiword.sh -s en -t hr -p ./baseline-factored-retagged-unk/model/phrase-table.0-0,1.gz -o ./baseline-factored-retagged-unk/model/phrase-table-morphexpandedmultiword-somecases.withtagprob.0-0,1.gz -w ./baseline-factored-retagged-unk/model/morph-expansionmulti-somecases.withtagprob-factored-withdebug/ -g /home/vmsanchez/software/abumatran-repo/tags_29-1-2016-somecases -l ./linguistic-data/apertium-hbs.hbs_HR_purist.mte.gz -c /home/vmsanchez/zagreb-2016/morphological-expansion/re-tagging/hrwac2.0.deduped.devert.norm.tok.true.esc.true.factored.hr.gz
```
The `-w` flag defines the working directory (where all the intermediate files are stored), while the `-c` flag specifies the monolingual
corpus from which the probability distribution of tags is computed.

Once the morphologically expanded phrase table has been created, you can tune and evaluate a system with the help of the aforementioned
`Makefile-trainmoses`. See `/home/vmsanchez/zagreb-2016/morphological-expansion/run-experiment-morphexpansionmulti-retagged-somecases-withtagprob-newff-multiref.sh` at our server for an example of how to tune the system. Note that it relies on a successful execution of the training and evaluation of the factored system. It also uses an additional feature function that
counts the the number of words with the special *Unk* morphosyntactic factor. A version of Moses modified with this new feature function can be found at our server: `/home/vmsanchez/software/mosesdecoder-RELEASE-3.0-newfactor`.

The morphologically expanded phrase table can be filtered in order to keep only some lexical categories. The script `morph-expand-scripts/filter-synthetic-phrase-table.sh` keeps only those entries with the following PoS: N,AN,NN,NCN,VN,PV.
You can change its behavior by locating that string and changing it.

## Lexicon integration

Another method for improving the system is enriching it with an external bilingual lexicon, which also
needs to be expanded. For instance, it contains only the base form of adjectives and nouns in Croatian.

The expansion of the lexicon and the creation of an additional phrase table that contains it
can be performed with the program `morph-expand-lexicon.sh`. This is an example call:
```
bash /home/vmsanchez/software/abumatran-repo/morph-expand-lexicon.sh -s en -t hr -i ./raw/EH.Txt -o /home/vmsanchez/zagreb-2016/morphological-expansion/baseline-factored-retagged-unk/model/phrase-table.newlexicon-filter-by-newrules-tokenized-slfilter-slexpand-removeadj.0-0,1.gz  -w ./work-filter-by-newrules-tokenized-slfilter-slexpand-removeadj/  -l /home/vmsanchez/zagreb-2016/morphological-expansion/linguistic-data/apertium-hbs.hbs_HR_purist.mte.sharelemma-adj-n.gz -L /home/vmsanchez/zagreb-2016/morphological-expansion/linguistic-data/morph_english.flat.gz  -m /home/vmsanchez/software/mosesdecoder-RELEASE-3.0  -e
```
`./raw/EH.Txt` is the bilingual lexicon
`-o` determines the output phrase table
`-w` determines the working directory, where all the intermediate files are stored
`-l` is the Croatian monolingual lexicon and -L is the English monolingual lexicon
`-m` defines the Moses installation directory (needed for creating the phrase table)
`-e` enables SL expansion (reccommended)

Once the lexicon has been expanded, there are multiple ways of integrating it in the system.
You can just add the result of the expansion to the training parallel corpus (the file `bilFactoredLexicon` that can be found
in the working directory contains tab-separated text already tokenized and escaped, ready to be concatenated to the training
parallel corpus).

You can also use the additional phrase table that has been created and train using the `Makefile-trainmoses` makefile. See file `/home/vmsanchez/zagreb-2016/morphological-expansion/run-experiment-retagged-newlexicon-multiref.sh` at our server for an example. Nevertheless, none of these two approaches allowed us to outperform the factored baseline.
