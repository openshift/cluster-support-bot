# Setup in OpenShift

```sh
oc new-app https://github.com/<project>/cluster-support-bot.git \
  -e APP_FILE=cluster-support-bot.py \
  -e BOT_ID=<bot ID -- hover over the bot name in Slack to get this> \
  -e SLACK_BOT_TOKEN=<token from https://api.slack.com/apps/XXXXXX/install-on-team?> \
  -e HYDRA_USER=<FIXME: how to get one of these> \
  -e HYDRA_PASSWORD=<FIXME: how to get one of these> \
  -e DASHBOARD=https://FIXME.example.com/somewhere-users-can-see-cluster-details?cluster-id=
```

Test by using `oc logs -f <podname>`to make sure it's running.
