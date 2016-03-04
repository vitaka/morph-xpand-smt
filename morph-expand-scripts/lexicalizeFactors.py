import sys,argparse

ENCODING="utf-8"

CLOSEDTAGS_ALWAYSLEX=set([u"Cc",u"Cs",u"Pd-fpa", u"Pd-fpd", u"Pd-fpg", u"Pd-fpi", u"Pd-fpl", u"Pd-fpn", u"Pd-fsa", u"Pd-fsd", u"Pd-fsg", u"Pd-fsi", u"Pd-fsl", u"Pd-fsn", u"Pd-mpa", u"Pd-mpd", u"Pd-mpg", u"Pd-mpi", u"Pd-mpl", u"Pd-mpn", u"Pd-msan", u"Pd-msay", u"Pd-msd", u"Pd-msg", u"Pd-msi", u"Pd-msl", u"Pd-msn", u"Pd-npa", u"Pd-npd", u"Pd-npg", u"Pd-npi", u"Pd-npl", u"Pd-npn", u"Pd-nsa", u"Pd-nsd", u"Pd-nsg", u"Pd-nsi", u"Pd-nsl", u"Pd-nsn", u"Pi3m-a", u"Pi3m-d", u"Pi3m-g", u"Pi3m-i", u"Pi3m-l", u"Pi3m-n", u"Pi3m-v", u"Pi3n-a", u"Pi3n-d", u"Pi3n-g", u"Pi3n-i", u"Pi3n-l", u"Pi3n-n", u"Pi3n-v", u"Pi-fpa", u"Pi-fpd", u"Pi-fpg", u"Pi-fpi", u"Pi-fpl", u"Pi-fpn", u"Pi-fpv", u"Pi-fsa", u"Pi-fsd", u"Pi-fsg", u"Pi-fsi", u"Pi-fsl", u"Pi-fsn", u"Pi-fsv", u"Pi-mpa", u"Pi-mpd", u"Pi-mpg", u"Pi-mpi", u"Pi-mpl", u"Pi-mpn", u"Pi-mpv", u"Pi-msan", u"Pi-msay", u"Pi-msd", u"Pi-msg", u"Pi-msi", u"Pi-msl", u"Pi-msn", u"Pi-msv", u"Pi-npa", u"Pi-npd", u"Pi-npg", u"Pi-npi", u"Pi-npl", u"Pi-npn", u"Pi-npv", u"Pi-nsa", u"Pi-nsd", u"Pi-nsg", u"Pi-nsi", u"Pi-nsl", u"Pi-nsn", u"Pi-nsv", u"Pi--sa", u"Pi--sd", u"Pi--sg", u"Pi--si", u"Pi--sl", u"Pi--sn", u"Pp1-pa", u"Pp1-pd", u"Pp1-pg", u"Pp1-pi", u"Pp1-pl", u"Pp1-pn", u"Pp1-pv", u"Pp1-sa", u"Pp1-sd", u"Pp1-sg", u"Pp1-si", u"Pp1-sl", u"Pp1-sn", u"Pp2-pa", u"Pp2-pd", u"Pp2-pg", u"Pp2-pi", u"Pp2-pl", u"Pp2-pn", u"Pp2-pv", u"Pp2-sa", u"Pp2-sd", u"Pp2-sg", u"Pp2-si", u"Pp2-sl", u"Pp2-sn", u"Pp2-sv", u"Pp3fpn", u"Pp3fsa", u"Pp3fsd", u"Pp3fsg", u"Pp3fsi", u"Pp3fsl", u"Pp3fsn", u"Pp3mpn", u"Pp3msa", u"Pp3msd", u"Pp3msg", u"Pp3msi", u"Pp3msl", u"Pp3msn", u"Pp3npn", u"Pp3nsa", u"Pp3nsd", u"Pp3nsg", u"Pp3nsi", u"Pp3nsl", u"Pp3nsn", u"Pp3-pa", u"Pp3-pd", u"Pp3-pg", u"Pp3-pi", u"Pp3-pl", u"Pq", u"Pq3m-a", u"Pq3m-d", u"Pq3m-g", u"Pq3m-i", u"Pq3m-l", u"Pq3m-n", u"Pq3n-a", u"Pq3n-d", u"Pq3n-g", u"Pq3n-i", u"Pq3n-l", u"Pq3n-n", u"Pq-fpa", u"Pq-fpd", u"Pq-fpg", u"Pq-fpi", u"Pq-fpl", u"Pq-fpn", u"Pq-fsa", u"Pq-fsd", u"Pq-fsg", u"Pq-fsi", u"Pq-fsl", u"Pq-fsn", u"Pq-mpa", u"Pq-mpd", u"Pq-mpg", u"Pq-mpi", u"Pq-mpl", u"Pq-mpn", u"Pq-msan", u"Pq-msay", u"Pq-msd", u"Pq-msg", u"Pq-msi", u"Pq-msl", u"Pq-msn", u"Pq-npa", u"Pq-npd", u"Pq-npg", u"Pq-npi", u"Pq-npl", u"Pq-npn", u"Pq-nsa", u"Pq-nsd", u"Pq-nsg", u"Pq-nsi", u"Pq-nsl", u"Pq-nsn", u"Ps1fpa", u"Ps1fpd", u"Ps1fpg", u"Ps1fpi", u"Ps1fpl", u"Ps1fpn", u"Ps1fpv", u"Ps1fsa", u"Ps1fsd", u"Ps1fsg", u"Ps1fsi", u"Ps1fsl", u"Ps1fsn", u"Ps1fsv", u"Ps1mpa", u"Ps1mpd", u"Ps1mpg", u"Ps1mpi", u"Ps1mpl", u"Ps1mpn", u"Ps1mpv", u"Ps1msan", u"Ps1msay", u"Ps1msd", u"Ps1msg", u"Ps1msi", u"Ps1msl", u"Ps1msn", u"Ps1msv", u"Ps1npa", u"Ps1npd", u"Ps1npg", u"Ps1npi", u"Ps1npl", u"Ps1npn", u"Ps1npv", u"Ps1nsa", u"Ps1nsd", u"Ps1nsg", u"Ps1nsi", u"Ps1nsl", u"Ps1nsn", u"Ps1nsv", u"Ps2fpa", u"Ps2fpd", u"Ps2fpg", u"Ps2fpi", u"Ps2fpl", u"Ps2fpn", u"Ps2fpv", u"Ps2fsa", u"Ps2fsd", u"Ps2fsg", u"Ps2fsi", u"Ps2fsl", u"Ps2fsn", u"Ps2fsv", u"Ps2mpa", u"Ps2mpd", u"Ps2mpg", u"Ps2mpi", u"Ps2mpl", u"Ps2mpn", u"Ps2mpv", u"Ps2msan", u"Ps2msay", u"Ps2msd", u"Ps2msg", u"Ps2msi", u"Ps2msl", u"Ps2msn", u"Ps2msv", u"Ps2npa", u"Ps2npd", u"Ps2npg", u"Ps2npi", u"Ps2npl", u"Ps2npn", u"Ps2npv", u"Ps2nsa", u"Ps2nsd", u"Ps2nsg", u"Ps2nsi", u"Ps2nsl", u"Ps2nsn", u"Ps2nsv", u"Ps3fpa", u"Ps3fpd", u"Ps3fpg", u"Ps3fpi", u"Ps3fpl", u"Ps3fpn", u"Ps3fpv", u"Ps3fsa", u"Ps3fsd", u"Ps3fsg", u"Ps3fsi", u"Ps3fsl", u"Ps3fsn", u"Ps3fsv", u"Ps3mpa", u"Ps3mpd", u"Ps3mpg", u"Ps3mpi", u"Ps3mpl", u"Ps3mpn", u"Ps3mpv", u"Ps3msan", u"Ps3msay", u"Ps3msd", u"Ps3msg", u"Ps3msi", u"Ps3msl", u"Ps3msn", u"Ps3msv", u"Ps3npa", u"Ps3npd", u"Ps3npg", u"Ps3npi", u"Ps3npl", u"Ps3npn", u"Ps3npv", u"Ps3nsa", u"Ps3nsd", u"Ps3nsg", u"Ps3nsi", u"Ps3nsl", u"Ps3nsn", u"Ps3nsv", u"Px-fpa", u"Px-fpd", u"Px-fpg", u"Px-fpi", u"Px-fpl", u"Px-fpn", u"Px-fsa", u"Px-fsd", u"Px-fsg", u"Px-fsi", u"Px-fsl", u"Px-fsn", u"Px-mpa", u"Px-mpd", u"Px-mpg",u"Px-mpi", u"Px-mpl", u"Px-mpn", u"Px-msan", u"Px-msay", u"Px-msd", u"Px-msg", u"Px-msi", u"Px-msl", u"Px-msn", u"Px-npa", u"Px-npd", u"Px-npg", u"Px-npi", u"Px-npl",u"Px-npn",u"Px-nsa", u"Px-nsd", u"Px-nsg", u"Px-nsi", u"Px-nsl", u"Px-nsn", u"Px--sa", u"Px--sd", u"Px--sg", u"Px--si", u"Px--sl", u"Qo", u"Qq", u"Qr", u"Qz", u"Sa", u"Sd", u"Sg", u"Si", u"Sl", u"Vaa1p", u"Vaa1s", u"Vaa2p", u"Vaa2s", u"Vaa3p", u"Vaa3s", u"Vae1p", u"Vae1s", u"Vae2p", u"Vae2s", u"Vae3p", u"Vae3s", u"Vaf3s", u"Vam1p", u"Vam2p", u"Vam2s", u"Van", u"Vap-pf", u"Vap-pm", u"Vap-pn", u"Vap-sf", u"Vap-sm", u"Vap-sn", u"Var1p", u"Var1s", u"Var2p", u"Var2s", u"Var3p", u"Var3s"])
CLOSEDTAGS_LEXADV=set([u"Rg",u"Rgc",u"Rgp",u"Rgs",u"Rr",u"Rs"])

parser=argparse.ArgumentParser(description="lexicalize morph factors for closed lexical categories")
parser.add_argument("--closed_adverbs")
parser.add_argument("--field",type=int)
args = parser.parse_args()

closedAdverbs_set=set()
for line in open(args.closed_adverbs):
	line=line.rstrip("\n").decode(ENCODING)
	#we ignore multi-word adverbs at the moment
	if u" " not in line:
		closedAdverbs_set.add(line)

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)

	if args.field != None:
		inputparts=line.split(u"\t")
		myinput=inputparts[args.field]
	else:
		myinput=line

	tokens=myinput.split(u" ")
	output_l=[]
	for token in tokens:
		parts=token.split(u"|")
		surface=parts[0]
		tag=parts[1]
		if tag in CLOSEDTAGS_ALWAYSLEX or tag in CLOSEDTAGS_LEXADV and surface.lower() in closedAdverbs_set:
			output_l.append(surface+u"|"+surface)
		else:
			output_l.append(token)

	if args.field != None:
		inputparts[args.field]=u" ".join(output_l)
		print u"\t".join( inputparts ).encode(ENCODING)
	else:
		print u" ".join(output_l).encode(ENCODING)
