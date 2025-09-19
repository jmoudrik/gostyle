import json
import sys


for a in sys.argv[1:]:
	print a
	with open(a,'r') as fin:
		data = json.load(fin)
	feed = data.get('feedback',None)
	if feed:
		print "    str:", data.get('str',"N/A")
		print "   feed:", feed
		print
		
	



