# proactive-support-bot

## Setup
```
oc new-app https://github.com/<project>/proactive-support-bot.git \
  -e APP_FILE=proactive-support-bot.py \
  -e SLACK_SIGNING_SECRET=<credentials from https://api.slack.com/apps/XXXXX/general?> \
  -e SLACK_BOT_TOKEN=<token from https://api.slack.com/apps/XXXXXX/install-on-team?> 
```

```
oc edit route proactive-support-bot
(add the following to the spec)
  tls:
    insecureEdgeTerminationPolicy: Redirect
    termination: edge
```

Test by using `oc logs -f <podname>`to make sure it's running.  You can hit it
with a browser to make sure the route is going through.

Edit https://api.slack.com/apps/XXXXX/event-subscriptions? and update the
request URL.  The url will be the route of the app + `/slack/events`.  You'll
wait for a minute or so and it will verify the new URL is working.  Once you
hit `Save changes` Slack will tell you to "reinstall" the app.
