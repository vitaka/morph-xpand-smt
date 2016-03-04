import sys,re

ENCODING="utf-8"

UNKTAG=u"Unk"

digitre=re.compile(u"\d",re.U)
nondigitre=re.compile(u"\D",re.U)

mdcre=re.compile(u"^[-]?\d*[\.,]?\d*$", re.U)
mdmre=re.compile(u"^[\d\.,-]+$", re.U)
ordinalre=re.compile(u"^[\d]+\.$",re.U)


#assigns proper digit tags to unknown words
def assignNumberTag(token):
	if digitre.search(token) != None:
		if ordinalre.match(token) != None:
			return u"Mdo"
		elif mdcre.match(token) != None:
			return u"Mdc"
		elif mdmre.match(token) != None:
			return u"Mdm"
		else:
			return u"Mds"
	else:
		#No tag change
		return None

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split("\t")
	tokens=parts[0].strip().split(" ")
	tags=parts[1].strip().split(" ")
	if len(tokens) != len(tags):
		print >>sys.stderr, "ERROR: Dirferent length of tokens and tags: "+line.encode(ENCODING)
		continue
	out_l=[]
	for token,tag in zip(tokens,tags):
		if tag == UNKTAG:
			#try to restore number tag
			numbertag=assignNumberTag(token)
			if numbertag != None:
				tag=numbertag
		out_l.append(token+u"|"+tag)
	print u" ".join(out_l).encode(ENCODING)
