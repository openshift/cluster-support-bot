# License

This project is distributed under [the Apache License Version 2.0][LICENSE].

# Development Environment

* go to slack.com and create a new workspace. For example, `< your name >`
* create your account and set your password
* go to https://api.slack.com/apps and create a new development app. Name can be something like `< yourname > cluster support`. Choose the workspace you just created.
* click on the app name and go to Bot Users. Add a development bot, for example, `cluster-support-bot`
* click on OAuth & Permissions and install the bot to your workspace
* copy the Bot User OAuth Access Token and export it to `SLACK_BOT_TOKEN`:

    ```sh
    export SLACK_BOT_TOKEN=xoxb-....
    ```

* click on Basic Information and copy the Signing Secret and export it to `SLACK_SIGNING_SECRET`:

    ```sh
    export SLACK_SIGNING_SECRET=1234....
    ```

* start the bot. It must be publicly accessible, so use a public OpenShift or perhaps ngrok
* click on Event Subscriptions. Turn on and paste in `< your app's url >/slack/events` You should get a green check mark. If not, make sure the env variables above are set and correct.
* subscribe to bot event `app_mention`
* join a channel and add the bot. Message the bot `@< botname > hi` and you should get a response
