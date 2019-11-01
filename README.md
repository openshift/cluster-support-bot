# Cluster-support Bot

A Slack bot for collaboration on per-cluster support issues.

Bot commands:

* `help`              Show this help
* `summary`           Summarize a cluster by ID
* `set-summary`       Set (or edit) the cluster summary
* `detail`            Upload a file to Slack with the cluster summary and all comments
* `comment`           Add a comment on a cluster by ID

## Setup in OpenShift

```sh
oc new-app https://github.com/<project>/cluster-support-bot.git \
  -e APP_FILE=cluster-support-bot.py \
  -e SLACK_SIGNING_SECRET=<credentials from https://api.slack.com/apps/XXXXX/general?> \
  -e SLACK_BOT_TOKEN=<token from https://api.slack.com/apps/XXXXXX/install-on-team?> \
  -e HYDRA_USER=<FIXME: how to get one of these> \
  -e HYDRA_PASSWORD=<FIXME: how to get one of these> \
  -e DASHBOARD=https://FIXME.example.com/somewhere-users-can-see-cluster-details?cluster-id=
```

```sh
oc edit route cluster-support-bot
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
