import sys


def rangeString(s):
    return sum(((list(range(*[int(j) + k for k,j in enumerate(i.split('-'))]))
         if '-' in i else [int(i)]) for i in s.split(',')), [])


def prompt(original, mapfunc=None, title='Choice', strm=sys.stdout, default=None):
    choices = original if not mapfunc else [mapfunc(c) for c in original]

    strm.write(title + "\n")
    for i in range(len(choices)):
        strm.write(" [{}] {}{}\n".format(i+1, choices[i], ' (default)' if default == i else ''))

    n_choices = len(choices)
    n_max = n_choices
    index = []

    while True:
        strm.write("Choice: ")
        try:
            index = rangeString(input())
        except:
            if default:
                index = [default]
                break

        print("INDEX", index, 0, n_max)
        if len(index) == 0 or min(index) <= 0 or max(index) > n_max:
            strm.write(" Please make a valid choice\n")
        else:
            break

    return [original[i] for i in index]


#https://metricsda.fibery.io/Product_Management/bug/File-sync-takes-too-long-(for-these-files)-433?sharing-key=27354285-96a6-4cc8-9c7a-4f8072c64587
