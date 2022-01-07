import re
import slackmailbot


class MergeRequests(slackmailbot.SlackMailBot):
    def __init__(self, debug=False, label="MergeRequests", broadcast=False):
        slackmailbot.SlackMailBot.__init__(self, label,
                                           broadcast=broadcast,
                                           debug=debug,
                                           application="merge_requests",
                                           name="MergeRequest")
        self.body = {
            'author!': re.compile('Author: (\S.*\S)'),
            'assignee': [re.compile('Assignee: (\S.*\S)'),
                         re.compile('Assignee changed from .* to (\S.*\S)')],
            'url': re.compile('https://gitlab.metrics.ca/\S+/-/merge_requests/\d+')
        }

        def getAuthor(data, thread):
            key = 'author!'
            if key in data and data[key]:
                return data[key][1]

            author = thread.getFrom()
            author = author.split('"')[1].strip() if '"' in author else author
            author = author.split('(')[0].strip()
            return author

        def actionFunc(thread, content):
            messages = [m for m in content['body'] if m['unread']]
            if len(messages) == 0:
                return

            message = messages[-1]
            title = thread.getSubject().split("|")[1].split('...')[0].strip()
            data = message['data']
            author = getAuthor(data, thread)

            assignee = data['assignee'][1]
            url = data['url'][0]
            content = "**{}**\n\n".format(title)
            content += "| Info     | Info   |\n"
            content += "|----------|----|\n"
            content += "| Author   | {} |\n".format(author)
            content += "| Assignee | {} |\n".format(assignee)
            content += "| Link     | {} |\n".format(url)
            content += "\n"
            title = "Merge Request from {}".format(author)

            return self.send(content,
                             broadcast=author,
                             emoji="reading", text=title)

        self.action = actionFunc
