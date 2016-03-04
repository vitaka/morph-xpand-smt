import sys, itertools, collections

def contains_sublist(lst, sublst):
	n = len(sublst)
	return any((sublst == lst[i:i+n]) for i in xrange(len(lst)-n+1))

class TagGroups:
	def __init__(self, fileobj):
		self.groups=[]
		self.mappings=dict()
		self.probs=dict()
		self.loadData(fileobj)

	def buildProbs(self,freqFile):
		freqsDict=dict()
		for line in freqFile:
			parts=line.rstrip(u"\n").split(u"\t")
			freq=int(parts[0])
			morphTag=parts[1]
			freqsDict[morphTag]=freq
		for group in self.groups:
			totalFreq=sum( [freqsDict[morphTag] if morphTag in freqsDict else 0 for morphTag in group ] )
			for morphTag in group:
				prob=0.0
				if morphTag in freqsDict:
					prob=freqsDict[morphTag]*1.0/totalFreq
				self.probs[morphTag]=prob

	def loadData(self,fileobj):
		for line in fileobj:
			tags=line.rstrip("\n").strip().split(u" ")
			newgroup=[]
			for tag in tags:
				newgroup.append(tag)
			for tag in newgroup:
				if tag in self.mappings:
					print >>sys.stderr, "WARNING: tag '"+unicode(tag).encode("utf-8")+"' belongs to multiple groups"
				self.mappings[tag]=newgroup
			self.groups.append(newgroup)

	def getProb(self,morphTag):
		return self.probs[morphTag] if morphTag in self.probs else 0.0

	def getGroup(self, tag):
		if tag in self.mappings:
			return self.mappings[tag]
		else:
			return None
	@staticmethod
	def groupToString(tagGroup):
		return u"__".join(tagGroup)

	@staticmethod
	def stringToGroup(tagGroupStr):
		return tagGroupStr.split(u"__")


class TagGroupsMulti:
	def __init__(self, fileobj):
		self.groups=[]
		self.mappings=dict()
		self.probs=dict()
		self.tagSet=set()
		self.analyzer=dict()
		self.loadData(fileobj)


	def buildProbs(self,freqFile):
		freqsDict=dict()
		for line in freqFile:
			parts=line.rstrip(u"\n").split(u"\t")
			freq=int(parts[0])
			morphTagSeq=tuple(parts[1].split(u"__"))
			freqsDict[morphTagSeq]=freq
		for group in self.groups:
			totalFreq=sum( [freqsDict[morphTag] if morphTag in freqsDict else 0 for morphTag in group ] )
			for morphTag in group:
				prob=0.0
				if morphTag in freqsDict:
					prob=freqsDict[morphTag]*1.0/totalFreq
				self.probs[morphTag]=prob

	#a tag group is a list of tuples (all the tuples must have the same length L)
	#each element of the tuple represents a sequence of L tags
	def loadData(self,fileobj):
		for line in fileobj:
			line=line.rstrip("\n").strip()
			if u"#" in line:
				line=line.split(u"#")[0].strip()
			if len(line) == 0:
				continue
			tags=line.split(u" ")
			newgroup=[]
			for tag in tags:
				newgroup.append(tuple(tag.split(u"__")))
			for tag in newgroup:
				if tag in self.mappings:
					print >>sys.stderr, "WARNING: tag '"+unicode(tag).encode("utf-8")+"' belongs to multiple groups"
				self.mappings[tag]=newgroup
			self.groups.append(newgroup)
		#build tag set
		for groupList in self.groups:
			for groupTuple in groupList:
				for i in range(len(groupTuple)):
					self.tagSet.add(groupTuple[i])

	def getProb(self,morphTag):
		if isinstance(morphTag,list):
			morphTag=tuple(morphTag)
		return self.probs[morphTag] if morphTag in self.probs else 0.0

	def getGroupWithLexUnits(self,tag_l,words):
		if isinstance(tag_l,list):
			tag=tuple(tag_l)
			if tag in self.mappings:
				return self.mappings[tag],tag_l
			else:
				#find the first tag group that matches by de-lexicalizing
				deLexicalizableIndexes=[]
				for i in range(len(tag_l)):
					if tag_l[i] == words[i]:
						deLexicalizableIndexes.append(i)
				deLexicalizableAlternatives=[]
				for deLexicalizableIndex in deLexicalizableIndexes:
					thisalternative=[]
					if tag_l[deLexicalizableIndex] in self.analyzer:
						thisalternative.extend(self.analyzer[tag_l[deLexicalizableIndex]])
					deLexicalizableAlternatives.append(thisalternative)
				#cartesian product
				for alternative in itertools.product(*deLexicalizableAlternatives):
					altList=[]
					altList.extend(tag_l)
					for i in range(len(alternative)):
						altList[deLexicalizableIndexes[i]]=alternative[i]
					tag=tuple(altList)
					if tag in self.mappings:
						return self.mappings[tag],altList
				return None,[]
		else:
			print >>sys.stderr, "ERROR: Input is not a list. Closing program"
			exit(1)

	def getGroup(self, tag):
		if isinstance(tag,list):
			tag=tuple(tag)
		if tag in self.mappings:
			return self.mappings[tag]
		else:
			return None

	def addLexicalizedMappings(self,it):
		for line in it:
			line=line.rstrip("\n")
			parts=line.split("\t")
			word=parts[0]
			tag=parts[1]
			if tag in self.tagSet:
				if not word in self.analyzer:
					self.analyzer[word]=[]
				self.analyzer[word].append(tag)

	@staticmethod
	def groupToStringList(tagGroup):
		output=[]
		lengthOfGroup=len(tagGroup[0])
		for i in range(lengthOfGroup):
			output.append(u"__".join( element[i] for element in tagGroup ))
		return output

	@staticmethod
	def stringToGroup(tagGroupStr):
		return tagGroupStr.split(u"__")


class Lexicon:
	def __init__(self, fileobj, mode=0, isEnglish=False):
		self.mapToLemma=dict()
		self.mapToSurface=dict()
		self.mapToLemmaTag=dict()
		self.mapToSurfaceTag=dict()
		if isEnglish:
			self.offset=1
			self.isMultiTag=True
		else:
			self.offset=0
			self.isMultiTag=False

		if mode == 1:
			self.loadGenerationLexicon(fileobj)
		elif mode == 2:
			self.loadTaggingLexicon(fileobj)
		elif mode == 3:
			self.loadLemmaLookupLexicon(fileobj)
		else:
			self.loadAnalysisLexicon(fileobj)

	def loadAnalysisLexicon(self,fileobj):
		for line in fileobj:
			if line.startswith(";;;"):
				continue
			line=line.strip()
			parts=line.split(u"\t")
			self.mapToLemma[(parts[0],parts[2+self.offset])]=parts[1+self.offset]

	def loadGenerationLexicon(self,fileobj):
		for line in fileobj:
			if line.startswith(";;;"):
				continue
			line=line.strip()
			parts=line.split(u"\t")
			if not (parts[1+self.offset],parts[2+self.offset]) in self.mapToSurface:
				self.mapToSurface[(parts[1+self.offset],parts[2+self.offset])]=[]
			self.mapToSurface[(parts[1+self.offset],parts[2+self.offset])].append(parts[0])

	def loadLemmaLookupLexicon(self,fileobj):
		for line in fileobj:
			if line.startswith(";;;"):
				continue
			line=line.strip()
			parts=line.split(u"\t")
			if not parts[1+self.offset] in self.mapToSurfaceTag:
				self.mapToSurfaceTag[parts[1+self.offset]]=[]
			if not self.isMultiTag:
				secondPart=parts[2+self.offset]
			else:
				secondPart=set()
				for adPart in parts[2+self.offset:]:
					secondPart.add(frozenset([t.split(u"#")[0] for t in adPart.split(u" ")]))
			self.mapToSurfaceTag[parts[1+self.offset]].append((parts[0].strip(), secondPart))

	def loadTaggingLexicon(self,fileobj):
		for line in fileobj:
			if line.startswith(";;;"):
				continue
			line=line.strip()
			parts=line.split(u"\t")
			if parts[0].strip() not in self.mapToLemmaTag:
				self.mapToLemmaTag[parts[0].strip()]=[]
			if self.isMultiTag:
				secondPart=set()
				for adPart in parts[2+self.offset:]:
					secondPart.add(frozenset([t.split(u"#")[0] for t in  adPart.split(u" ")]))
			else:
				secondPart=parts[2+self.offset]

			self.mapToLemmaTag[parts[0].strip()].append((parts[1+self.offset],secondPart))

	def getLemmaTag(self,surface):
		if surface in self.mapToLemmaTag:
			return self.mapToLemmaTag[surface]
		else:
			return None

	def getLemma(self,surface,morphTag):
		if (surface,morphTag) in self.mapToLemma:
			return self.mapToLemma[(surface,morphTag)]
		else:
			return None

	def getSurfaceTag(self,lemma):
		if lemma in self.mapToSurfaceTag:
			return self.mapToSurfaceTag[lemma]
		else:
			return None

	def getSurface(self,lemma,tag):
		if (lemma,tag) in self.mapToSurface:
			return self.mapToSurface[(lemma,tag)]
		else:
			return None

PhraseEntry = collections.namedtuple('PhraseEntry', ['tlsurface', 'tltags', 'tllemmas' , 'origin'])
class PhraseTable:
	UNKTAG=u"Unk"
	MAXN=7
	def __init__(self,fileobj=None, lexicon=None):
		self.phrasedict=dict()
		if fileobj != None:
			self.loadData(fileobj,lexicon)
		self.initCounts()

	def loadData(self,fileobj, lexicon):
		for line in fileobj:
			line=line.rstrip(u"\n").strip()
			parts=line.split(u" ||| ")
			slphrase=parts[0]
			splitTltokens=[tok.split(u"|") for tok in parts[1].split(u" ")]
			tlsurface=[tok[0] for tok in splitTltokens]
			tltags=[tok[1] for tok in splitTltokens]
			tllemmas=[]
			if lexicon != None:
				tllemmas=[ lexicon.getLemma(tok[0],tok[1]) for tok in splitTltokens ]
				for i in range(len(tllemmas)):
					if tllemmas[i] == None:
						tllemmas[i]=PhraseTable.UNKTAG
			origin=parts[-1]

			if not slphrase in self.phrasedict:
				self.phrasedict[slphrase]=[]
			self.phrasedict[slphrase].append(PhraseEntry(tlsurface,tltags,tllemmas,origin))

	def initCounts(self):
		#We will count:
		# - how many times each SL phrase has been observed in the dev set
		# - how many times each origin has generated a phrase found in the reference
		self.countsSL=collections.defaultdict(int)
		self.countsOriginMatch=collections.defaultdict(int)
		self.countsOriginMatchLemmatized=collections.defaultdict(int)

	def count_coverage(self,sltokens,tltokens_ll, tltokens_lem_ll = None, tltokens_tags_ll = None):
		for i in xrange(len(sltokens)):
			for size in xrange(1,PhraseTable.MAXN+1):
				if i+size <=len(sltokens):
					slphrase=u" ".join(sltokens[i:i+size])
					if slphrase in self.phrasedict:
						self.countsSL[slphrase]+=1
						#now check how many tl phrases are in the reference (or in any of the references if we have multiple ones)
						for pe in self.phrasedict[slphrase]:
							exactMatch=False
							if tltokens_tags_ll == None:
								if any( contains_sublist(tltokens,pe.tlsurface) for tltokens in tltokens_ll):
									exactMatch = True
							else:
								if any( contains_sublist(zip(tltokens,tltokens_tags),zip(pe.tlsurface,pe.tltags)) for tltokens,tltokens_tags in zip(tltokens_ll,tltokens_tags_ll)):
									exactMatch = True
							if exactMatch:
								self.countsOriginMatch[ (slphrase,pe.origin, u"__".join(surf+u"|"+tag for surf,tag in  zip(pe.tlsurface,pe.tltags) ) )  ]+=1
							if all( tllemma != PhraseTable.UNKTAG for tllemma in  pe.tllemmas ):
								if any( contains_sublist(tltokenslem,pe.tllemmas) for tltokenslem in tltokens_lem_ll):
									self.countsOriginMatchLemmatized[ (slphrase,pe.origin, u"__".join(surf+u"|"+tag for surf,tag in  zip(pe.tlsurface,pe.tltags) ) )     ]+=1

	def add_results(self, otherpt):
		for slphrase in otherpt.countsSL:
			self.countsSL[slphrase]+=otherpt.countsSL[slphrase]
		for key in otherpt.countsOriginMatch:
			self.countsOriginMatch[key]+=otherpt.countsOriginMatch[key]
		for key in otherpt.countsOriginMatchLemmatized:
			self.countsOriginMatchLemmatized[key]+=otherpt.countsOriginMatchLemmatized[key]

	def summary_coverage(self):
		for slphrase, origin, tltags in self.countsOriginMatch:
			freqLemmatized=0
			if (slphrase,origin,tltags) in self.countsOriginMatchLemmatized:
				freqLemmatized=self.countsOriginMatchLemmatized[(slphrase,origin,tltags)]
			yield u"\t".join([slphrase,origin,tltags,unicode(self.countsSL[slphrase]),unicode(freqLemmatized),unicode(self.countsOriginMatch[(slphrase,origin,tltags)]) ])
		for slphrase, origin, tltags in self.countsOriginMatchLemmatized:
			if (slphrase, origin, tltags) not in self.countsOriginMatch:
				yield u"\t".join([slphrase,origin,tltags,unicode(self.countsSL[slphrase]),unicode(self.countsOriginMatchLemmatized[(slphrase,origin,tltags)]),unicode(0) ] )
