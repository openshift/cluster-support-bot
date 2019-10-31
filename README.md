# proactive-support-bot

A slack bot for collaboration on per-cluster support issues.

Bot commands:

`help`              Show this help  
`summary`           Summarize a cluster by ID  
`set-summary`       Set (or edit) the cluster summary  
`detail`            Upload a file to Slack with the cluster summary and all comments  
`comment`           Add a comment on a cluster by ID  


## Setup in OpenShift

```sh
oc new-app https://github.com/<project>/proactive-support-bot.git \
  -e APP_FILE=proactive-support-bot.py \
  -e SLACK_SIGNING_SECRET=<credentials from https://api.slack.com/apps/XXXXX/general?> \
  -e SLACK_BOT_TOKEN=<token from https://api.slack.com/apps/XXXXXX/install-on-team?> \
  -e HYDRA_USER=<FIXME: how to get one of these> \
  -e HYDRA_PASSWORD=<FIXME: how to get one of these> \
  -e DASHBOARD=https://FIXME.example.com/somewhere-users-can-see-cluster-details?cluster-id=
```

```sh
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

## Development Environment
 * go to slack.com and create a new workspace. For example, "< your name >"
 * create your account and set your password
 * go to https://api.slack.com/apps and create a new development app. Name can be something like "< yourname > proactive support". Choose the workspace you just created.
 * click on the app name and go to Bot Users. Add a development bot, for example, "proactive-support-bot"
 * click on OAuth & Permissions and install the bot to your workspace
 * copy the Bot User OAuth Access Token and export it to SLACK_BOT_TOKEN:

    export SLACK_BOT_TOKEN=xoxb-....
 * click on Basic Information and copy the Signing Secret and export it to SLACK_SIGNING_SECRET

    export SLACK_SIGNING_SECRET=1234....
 * start the bot. It must be publicly accessible, so use a public OpenShift or perhaps ngrok
 * click on Event Subscriptions. Turn on and paste in < your app's url >/slack/events  You should get a green check mark. If not, make sure the env variables above are set and correct.
 * subscribe to bot event "app_mention"
 * join a channel and add the bot. Message the bot "@< botname > hi" and you should get a response
