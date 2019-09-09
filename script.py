import os
import json
path=os.getcwd()

folders=[]
files=[]
account={}


for pname,dname,fname in os.walk(path):
	for folder in dname:
		folders.append(os.path.join(pname,folder))

for fname in  folders:
	for file in  os.listdir(fname):
		if '.yaml' in file:
			account[os.path.basename(fname)]=os.path.join(fname,file).replace(os.getcwd(),"")

#print (account)
account_json=json.dumps(account)
	
print (account_json)