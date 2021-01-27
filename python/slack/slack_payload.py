#!/usr/bin/python

import select
import json
import getopt
import sys
from slack_config import SlackConfig

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(
                sys.argv[1:], "c:u:t:e:i:j",
                ["channel=", "username=", "text=", "emoji=", "icon=", "json"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    result = {}

    emoji = None
    useJson = False
    for o, a in opts:
        if o in ("-c", "--channel"):
            result["channel"] = a
        elif o in ("-u", "--username"):
            result["username"] = a
        elif o in ("-t", "--text"):
            result["text"] = a
        elif o in ("-e", "--emoji"):
            result["icon_emoji"] = ":{}:".format(a)
        elif o in ("-i", "--icon"):
            result["icon_url"] = a
        elif o in ("-j", "--json"):
            useJson = True

    # Resolve the channel if a nickname was used.
    cfg = SlackConfig()
    if 'channel' in result:
        result['channel'] = cfg.nickname(result['channel'])

    if select.select([sys.stdin, ], [], [], 0.0)[0]:
        for line in sys.stdin:
            if (useJson):
                result["blocks"] = json.loads(line)
            else:
                if "text" not in result:
                    result["text"] = ''

                result["text"] += line + "\n"

    print(json.dumps(result))
