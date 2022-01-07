import re
import slackmailbot


DEFAULT_STATUS = "\S+" #"Bug|Task|ToDo|Support|TestReq|Feature"

DEFAULT_EMOJIS = {'Bug': 'beetle',
                  'Task': 'white_check_mark',
                  'ToDo': 'spiral_note_pad',
                  'Support': 'wrench',
                  'TestReq': 'page_facing_up',
                  'Feature': 'gift',
                  'other': 'exclamation'}


class RedmineNotice(slackmailbot.SlackMailBot):
    def __init__(self, status=None, debug=False, broadcast=False,
                 label="Redmine", me=None):
        slackmailbot.SlackMailBot.__init__(self, label,
                                           broadcast=broadcast,
                                           debug=debug,
                                           application="redmine_notice",
                                           name="Redmine")
        if status:
            if isinstance(status, list):
                status = "|".join(status)
            elif not isinstance(status, str):
                status = str(status)
        else:
            status = DEFAULT_STATUS

        self.subjects = [re.compile("(({}) #(\d+))\] (.+)".format(status))]
        self.body = {
            'status': re.compile('Status: (\w+)'),
            'url': re.compile('https://portal.metrics.ca/issues/\d+'),
            'reporter': [re.compile('reported by (\S+( \S+?)*)\.'),
                         re.compile('Author: (\S.*\S)')],
            'assignee': re.compile('Assignee: (\S.*\S)')
        }
        self.email = self.getEmail()
        self.me = me

        def actionFunc(thread, content):
            messages = [m for m in content['body'] if m['unread']]
            if len(messages) == 0:
                return True

            message = messages[-1]
            data = message['data']
            category = content['subject'][2]
            identity = content['subject'][1]
            title = content['subject'][4]
            status = data['status'][1]
            reporter = data['reporter'][1]
            assignee = data['assignee'][1]
            if reporter == self.me:
                self.debugMsg("    Ignored", "Created By Me")
                return False

            if assignee != self.me:
                self.debugMsg("    Ignored", "Not Assigned To Me")
                return False

            url = data['url'][0]
            content = "**{}**\n\n".format(identity)
            content += "| Title    | {} |\n".format(title)
            content += "|----------|----|\n"
            content += "| Status   | {} |\n".format(status)
            content += "| Reporter | {} |\n".format(reporter)
            content += "| Assignee | {} |\n".format(assignee)
            content += "| Link     | {} |\n".format(url)

            emoji = DEFAULT_EMOJIS['other']
            if category in DEFAULT_EMOJIS:
                emoji = DEFAULT_EMOJIS[category]

            return self.send(content,
                             broadcast=reporter,
                             emoji=emoji, text=title)

        self.action = actionFunc
