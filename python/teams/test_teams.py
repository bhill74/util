import teams
import sys

s = teams.ToTeams()
#s.to(['A', 'B', 'C'], channel='me', text="Other")

content=[]
for l in sys.stdin:
    content.append(l)
s.to(content, channel='me', text="Other")
