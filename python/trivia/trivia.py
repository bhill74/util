import gdrive
import gsheets
import secrets

gd = gdrive.GDrive('fromdrive')
file = gd.resolve('Trivia/Trivia Questions')

ss = gsheets.GSpreadsheet(application="tosheets", gid=file[0].gid)
headers = ss.retrieve("A1:1")
if len(headers) == 0:
    print("No headers")
    exit(2)

headers = headers[0]
last_column = chr(ord('A')+len(headers)-1)
used_column = headers.index("Used") + 1
approved_column = headers.index("Approved") + 1

data = ss.retrieve("A2:"+last_column)

# Make sure each row is indexed
data = [[i+2] + data[i] for i in range(len(data))]

# Only keep those that are approved
valid = [d for d in data
         if len(d) > approved_column and d[approved_column] == 'Yes']


avail = [d for d in data
         if len(d) <= used_column or d[used_column] != 'Yes']

# Pick a random one from the list.
if len(avail) == 0:
    print("There are no questions to choose from")
    exit(2)

row = secrets.choice(avail)
print("Question: {}".format(row[3]))
print("Answer: {}".format(row[4]))

# Update the main spreadsheet
used = chr(ord('A')+used_column-1)
address = "{}{}".format(used, row[0])
ss.update([['Yes']], address)
