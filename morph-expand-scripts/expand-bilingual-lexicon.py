import sys,codecs, gzip, argparse, itertools
from morphExpansionUtils import TagGroupsMulti,Lexicon
ENCODING="utf-8"

VERBTAGS=set(u"Vmr1s Vmr2s Vmr1p Vmr2p Vmr3p Vmr1s-y Vmr2s-y Vmr1p-y Vmr2p-y Vmr3p-y Vmm2p Vmm2s Vmm2p-y Vmm2s-y".split(u" "))

VERBTAGSPLUS3PS=set(VERBTAGS)
VERBTAGSPLUS3PS.add(u"Vmr3s")

VERBTAGSPASTSIMPLE=set(u"Vma1p Vma1s Vma2p Vma2s Vma3p Vma3s Vme1p-y Vme1s-y Vme2p-y Vme2s-y Vme3p-y Vme3s-y Vme1p Vme1s Vme2p Vme2s Vme3p Vme3s Vmp-pf Vmp-pm Vmp-pn Vmp-sf Vmp-sm Vmp-sn Vmp-pfy Vmp-pmy Vmp-pny Vmp-sfy Vmp-smy Vmp-sny".split(u" "))
VERBTAGSPASTPART=set(u"Appfpay Appfpiy Appfpny Appfsay Appfsiy Appfsny Appmpay Appmpiy Appmpny Appmsann Appmsany Appmsayn Appmsayy Appmsdn Appmsgn Appmsiy Appmsln Appmsnn Appmsny Appmsvn Appnpay Appnpiy Appnpny Appnsay Appnsdn Appnsgn Appnsiy Appnsln Appnsny".split(u" "))

ALLOWEDCASES=set([u"n",u"a",u"i"])

PLURALNOUNS=set(u"Ncfpa Ncfpi Ncfpn Ncmpa Ncmpi Ncmpn Ncnpa Ncnpi Ncnpn Npfpa Npfpi Npfpn Npmpa Npmpi Npmpn Npnpa Npnpi Npnpn".split(u" "))

SINGULARASP=set(u"Aspfsay Aspfsiy Aspfsny Aspmsann Aspmsany Aspmsayy Aspmsiy Aspmsnn Aspnsay Aspnsiy Aspnsny".split(u" "))
PLURALASP=set(u"Aspfpay Aspfpiy Aspfpny Aspmpay Aspmpiy Aspmpny Aspnpay Aspnpiy Aspnpny".split(u" "))

DEBUG=False

def expand_past_and_participle(allSlTags,lexiconGeneration,lemma,tag):

	if DEBUG:
		print >> sys.stderr, "Expanding past and participle with:"
		print >> sys.stderr, "allSlTags: "+unicode(allSlTags).encode(ENCODING)
		print >> sys.stderr, "lemma: "+ lemma.encode(ENCODING)
		print >> sys.stderr, "tag: "+ unicode(tag).encode(ENCODING)

	#if tag == None, we don't do any check
	newPairs=[]
	if u"PAST" in allSlTags:
		# what happens if we have only a TL tag for past simple, but the SL word is also past participle?
		#Now it is generated
		#if tag in VERBTAGSPASTSIMPLE, inflect the lemma according to all the tags from VERBTAGSPASTSIMPLE
		if tag == None or tag in VERBTAGSPASTSIMPLE or tag in VERBTAGSPASTPART:
			for newtag in VERBTAGSPASTSIMPLE:
				if newtag != tag:
					newsurface_l=lexiconGeneration.getSurface(lemma,newtag)
					if newsurface_l != None:
						for newsurface in newsurface_l:
							newPairs.append((newsurface,newtag))

	if u"PASTPART" in allSlTags:
		#if tag in VERBTAGSPASTPART, inflect the lemma according to all the tags from VERBTAGSPASTPART
		if tag == None or tag in VERBTAGSPASTSIMPLE or tag in VERBTAGSPASTPART:
			for newtag in VERBTAGSPASTPART:
				if newtag != tag:
					newsurface_l=lexiconGeneration.getSurface(lemma,newtag)
					if newsurface_l != None:
						for newsurface in newsurface_l:
							newPairs.append((newsurface,newtag))
	return newPairs

parser=argparse.ArgumentParser(description="replace inflected forms with lemmas and set of possible tags")
parser.add_argument("--lexicon")
parser.add_argument("--lexicon_sl")
#this is no longer used
#parser.add_argument("--tag_groups")
parser.add_argument("--debug",action='store_true')
#parser.add_argument("--tag_freqs")
parser.add_argument('--expand_sl', action='store_true')
parser.add_argument('--remove_adj', action='store_true')

args = parser.parse_args()

DEBUG=args.debug

myreader=codecs.getreader(ENCODING)
myreader2=codecs.getreader(ENCODING)
myreader3=codecs.getreader(ENCODING)
myreader4=codecs.getreader(ENCODING)
myreader5=codecs.getreader(ENCODING)
lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')), 2)
lexiconAllInflections=Lexicon(myreader3(gzip.open(args.lexicon,'rb')), 3)
lexiconGeneration=Lexicon(myreader2(gzip.open(args.lexicon,'rb')), 1)
lexiconSL=Lexicon(myreader4(gzip.open(args.lexicon_sl,'rb')), 2, True)
lexiconSLAllInflections=Lexicon(myreader5(gzip.open(args.lexicon_sl,'rb')), 3, True)
#tagGroups=TagGroupsMulti(codecs.open(args.tag_groups,'r',ENCODING))
#tagGroups.buildProbs(codecs.open(args.tag_freqs,'r',ENCODING))

if False:
	if args.debug:
		print >>sys.stderr, str(len(lexicon.mapToLemmaTag))+" entries in tagging lexicon"
		print >>sys.stderr, str(len(lexiconAllInflections.mapToSurfaceTag))+" entries in lemma lookup lexicon"
		print >> sys.stderr, "These are the keys in lemma lookup lexicon:"
		for key in lexiconAllInflections.mapToSurfaceTag:
			print >> sys.stderr, key.encode(ENCODING)

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split("\t")
	#we already know this is a sigle word

	tlword=parts[1]

	slwords=parts[0].split(u" ")
	slAnalyses=None
	allSlTags=set()
	if len(slwords) == 1:
		slAnalyses=lexiconSL.getLemmaTag(slwords[0])
		if slAnalyses != None:
			for lemma,tags_ss in slAnalyses:
				for tags in tags_ss:
					allSlTags|=tags

	#check whether it is a lemma
	surfaceTag_l = lexiconAllInflections.getSurfaceTag(tlword)

	#if args.debug:
	#	print >> sys.stderr, (u"  surfaceTag_l: "+unicode(surfaceTag_l)).encode(ENCODING)
	if surfaceTag_l != None:
		if args.debug:
			#check whether it is also a surface. It is useful to decide what to do in this case
			lemmaTag_l = lexicon.getLemmaTag(tlword)
			if lemmaTag_l != None:
				print >>sys.stderr, "Lemma and surface at the same time: "+parts[0].encode(ENCODING)+" -> "+parts[1].encode(ENCODING)+" ("+ u" ".join([ lemma+u"|"+tag for lemma,tag in lemmaTag_l ]).encode(ENCODING)+")"

		#Rules:
		#Only singular nouns unless there are not singular infleccted forms
		#Only positive adverbs and adverbs
		#Only these tags for verbs:  Vmr1s Vmr2s Vmr1p Vmr2p Vmr3p Vmr1s-y Vmr2s-y Vmr1p-y Vmr2p-y Vmr3p-y Vmm2p Vmm2s Vmm2p-y Vmm2s-y

		#First we split entries by first letter of tag, and process them independently
		inflectedFormsByPOS=dict()
		for surface,tag in surfaceTag_l:
			POS=tag[0]
			if not POS in inflectedFormsByPOS:
				inflectedFormsByPOS[POS]=[]
			inflectedFormsByPOS[POS].append((surface,tag))

		if args.remove_adj and u"A" in inflectedFormsByPOS and len(inflectedFormsByPOS[u"A"]) > 10:
			continue

		nounFound=False
		if u"N" in inflectedFormsByPOS:
			nounFound=True

		verbFound=False
		if u"V" in inflectedFormsByPOS:
			verbFound=True
			if u"INF" not in allSlTags and len(allSlTags) > 0:
				#when TL is infinitve and SL is not infinitive, we don't follow the general rule for infinitives
				del inflectedFormsByPOS[u"V"]
				#if SL is past or past participle, apply expansion rules
				newPairs=expand_past_and_participle(allSlTags,lexiconGeneration,tlword,None)
				for surface, tag in newPairs:
					print  u"{0}\t{1}|{2}".format(parts[0],surface,tag).encode(ENCODING)


		allowedEntries=[]
		for POS in inflectedFormsByPOS:
			candidates=inflectedFormsByPOS[POS]
			#do filtering for nouns, adjectives, verbs and adverbs. Otherwise, print everything
			if POS == u"N":
				#first, find singular nouns
				filteredBySingular=[ (surface,tag) for surface,tag in candidates if ( tag[4] in ALLOWEDCASES and tag[3] == u"s"  ) ]
				if len(filteredBySingular) > 0:
					allowedEntries.extend(filteredBySingular)
				else:
					#only those filtered by case
					allowedEntries.extend([(surface,tag) for surface,tag in candidates if  tag[4] in ALLOWEDCASES ])
			elif POS == u"A":
				for surface,tag in candidates:
					if tag[2] == u"p" and tag[5] in ALLOWEDCASES and (not verbFound or not tag.startswith(u"App")) and (not nounFound or not tag.startswith(u"Asp")):
						allowedEntries.append((surface,tag))
			elif POS == u"V":
				for surface,tag in candidates:
					if tag in VERBTAGS:
						allowedEntries.append((surface,tag))
			elif POS == u"R":
				for surface,tag in candidates:
					if (len(tag) < 3 or  tag[2] == u"p" ) and ( not verbFound or ( tag[1] != u"r" and tag[1] != u"s" ) ):
						allowedEntries.append((surface,tag))
			else:
				allowedEntries.extend(candidates)

		for surface,tag in allowedEntries:
			print  u"{0}\t{1}|{2}".format(parts[0],surface,tag).encode(ENCODING)

		#expand SL
		if args.expand_sl:
			#3ps verbs (from infinitve). Croatian tag = Vmr3s
			#+ ing, Croatian: present tenses + Rr or Rs (the one we find in the lexicon)
			if args.debug:
				print >> sys.stderr, "Trying to expand SL"

			if slAnalyses != None and  verbFound:
				#1. find SL analyses that represent vebs in infinitive
				infinitiveSLAn=[ (lemma,tags_ss) for lemma,tags_ss in slAnalyses if any( (u"V" in tags and u"INF" in tags) for tags in tags_ss ) ]
				if args.debug:
					print >> sys.stderr, "Trying to expand SL for verb"
					print >> sys.stderr, "Infinitive forms of SL: "+unicode(infinitiveSLAn).encode(ENCODING)
				for sllemma,sltags_ss in infinitiveSLAn:
					#2. for each of them, generate
					#    - 3ps in English and Vmr3s in Croatian, and
					#    - +ing in English + present tenses (including 3person singular),Rr, Rs in Croatian
					sl3psforms=[]
					slIngforms=[]
					inflectedFormsSl=lexiconSLAllInflections.getSurfaceTag(sllemma)
					if inflectedFormsSl != None:
						for surfacesl,tagssl_ss in inflectedFormsSl:
							if any((u"PRES" in tagssl and u"V" in tagssl and u"3sg" in tagssl) for tagssl in tagssl_ss):
								sl3psforms.append(surfacesl)
							if any( (u"PROG" in tagssl and u"V" in tagssl) for tagssl in tagssl_ss ):
								slIngforms.append(surfacesl)
						tl3psForms=[]
						newsf3ps= lexiconGeneration.getSurface(tlword,u"Vmr3s")
						if newsf3ps != None:
							for sf in newsf3ps:
								tl3psForms.append((sf,u"Vmr3s"))
						tlingForms=[]
						for tltag in list(VERBTAGSPLUS3PS)+[u"Rr",u"Rs"]:
							localnewsfing=lexiconGeneration.getSurface(tlword,tltag)
							if localnewsfing != None:
								for sf in localnewsfing:
									tlingForms.append((sf,tltag))
						for slform in sl3psforms:
							for tlsf,tltag in tl3psForms:
								#TODO: retokenize SL side
								print  u"{0}\t{1}|{2}".format(slform,tlsf,tltag).encode(ENCODING)
						for slform in slIngforms:
							for tlsf,tltag in tlingForms:
								#TODO: retokenize SL side
								print  u"{0}\t{1}|{2}".format(slform,tlsf,tltag).encode(ENCODING)

			#plural form of nouns.
			#nouns + genitive in English -> possessive-adjective form Asp. only 3 cases, number of adj = number of noun
			if slAnalyses != None:
				#1. find SL analyses that represent singular nouns
				nounsgSLAn=[ (lemma,tags_ss) for lemma,tags_ss in slAnalyses if any((u"N" in tags and u"3sg" in tags and not u"GEN" in tags) for tags in tags_ss ) ]
				if args.debug:
					print >> sys.stderr, "Trying to expand SL for noun"
					print >> sys.stderr, "singular noun forms of SL: "+unicode(nounsgSLAn).encode(ENCODING)
				for sllemma,sltags_ss in nounsgSLAn:
					#2. generate plural, singular-genitive and plural-genitive
					slplForms=[]
					slsgGenForms=[]
					slplGenForms=[]
					inflectedFormsSl=lexiconSLAllInflections.getSurfaceTag(sllemma)
					if args.debug:
						print >> sys.stderr, "inflected forms SL: "+unicode(inflectedFormsSl).encode(ENCODING)
					if inflectedFormsSl != None:
						for surfacesl,tagssl_ss in inflectedFormsSl:
							if any((u"N" in tagssl and u"3pl" in tagssl and not u"GEN" in tagssl) for tagssl in tagssl_ss):
								slplForms.append(surfacesl)
							if any((u"N" in tagssl and u"3pl" in tagssl and u"GEN" in tagssl) for tagssl in tagssl_ss):
								slplGenForms.append(surfacesl)
							if any((u"N" in tagssl and u"3sg" in tagssl and u"GEN" in tagssl) for tagssl in tagssl_ss):
								slsgGenForms.append(surfacesl)
						tlplForms=[]
						for tltag in PLURALNOUNS:
							localnewsftlpl=lexiconGeneration.getSurface(tlword,tltag)
							if localnewsftlpl != None:
								for sf in localnewsftlpl:
									tlplForms.append((sf,tltag))

						tlsgGenForms=[]
						for tltag in SINGULARASP:
							localnewtlsggen=lexiconGeneration.getSurface(tlword,tltag)
							if localnewtlsggen != None:
								for sf in localnewtlsggen:
									tlsgGenForms.append((sf,tltag))

						tlplGenForms=[]
						for tltag in PLURALASP:
							localnewtlplgen=lexiconGeneration.getSurface(tlword,tltag)
							if localnewtlplgen != None:
								for sf in localnewtlplgen:
									tlplGenForms.append((sf,tltag))

						if args.debug:
							print >> sys.stderr, "slplForms: "+unicode(slplForms).encode(ENCODING)
							print >> sys.stderr, "slplGenForms: "+unicode(slplGenForms).encode(ENCODING)
							print >> sys.stderr, "slsgGenForms: "+unicode(slsgGenForms).encode(ENCODING)
							print >> sys.stderr, "tlplForms: "+unicode(tlplForms).encode(ENCODING)
							print >> sys.stderr, "tlsgGenForms: "+unicode(tlsgGenForms).encode(ENCODING)
							print >> sys.stderr, "tlplGenForms: "+unicode(tlplGenForms).encode(ENCODING)


						#combine and print
						for slform in slplForms:
							for tlsf,tltag in tlplForms:
								print  u"{0}\t{1}|{2}".format(slform,tlsf,tltag).encode(ENCODING)
						for slform in slsgGenForms:
							for tlsf,tltag in tlsgGenForms:
								print  u"{0}\t{1}|{2}".format(slform,tlsf,tltag).encode(ENCODING)
						for slform in slplGenForms:
							for tlsf,tltag in tlplGenForms:
								print  u"{0}\t{1}|{2}".format(slform,tlsf,tltag).encode(ENCODING)

	else:
		#if it is not a lemma, we analyse it assuming it is a surface form
		#and generate all the alternatives

		lemmaTag_l = lexicon.getLemmaTag(tlword)
		#if args.debug:
		#	print >> sys.stderr, (u"  lemmaTag_l: "+unicode(lemmaTag_l)).encode(ENCODING)
		if lemmaTag_l != None:
			#Rule: prefer Appmsvn over Vmn Only if participle is indefinite (7th char = n)
			#In other words, remove Vmn if there is an App???n*
			if len([ tag for lemma,tag in lemmaTag_l if (tag.startswith(u"App") and tag[6] ==u"n" ) ])  > 0:
				#remove Vmn
				filteredLemmaTag_l=[ (lemma,tag) for lemma,tag in lemmaTag_l if tag != u"Vmn" ]
			else:
				filteredLemmaTag_l=lemmaTag_l

			for lemma, tag in filteredLemmaTag_l:
				print  u"{0}\t{1}|{2}".format(parts[0],parts[1],tag).encode(ENCODING)

				#check whether we can expand past simple/past participle
				newPairs=expand_past_and_participle(allSlTags,lexiconGeneration,lemma,tag)
				for surface, tag in newPairs:
					print  u"{0}\t{1}|{2}".format(parts[0],surface,tag).encode(ENCODING)
