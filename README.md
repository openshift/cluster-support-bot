# Cluster-support Bot

A Slack bot for collaboration on per-cluster support issues.

## Explain available commands

Ask the bot to explain avialable commands:

```
@cluster-support-bot help
```

The bot will respond with documentation for the available commands.

## Get a support summary for a cluster

When you notice a problem with a cluster, ask the bot for the current summary:

```
@cluster-support-bot summary 09d9436d-52bb-48ba-9026-2ab047158ef6
```

The bot will respond with the current cluster summary, if any.
If the existing summary looks good, you don't have to do anything else.
If the summary looks stale or is missing, you can [update it](#set-a-support-summary-for-a-cluster).
You can also [get the detailed history](#get-the-detailed-support-history-for-a-cluster) of support discussion for that cluster.

## Set a support summary for a cluster

When the current summary is missing or stale, ask the bot to set a new summary:

```
@cluster-support-bot set-summary 09d9436d-52bb-48ba-9026-2ab047158ef6
This is your subject, e.g. Cluster appears to have misconfigured ingress DNS
This is your body, e.g. The ingress operator has not been configured to manage DNS
records for *.apps, but it is attempting to resolve them to see whether the user-provided
records are functional for cluster components.  The attempted resolution is failing,
so cluster admins should add the missing records.
```

The bot will post the summary to the customer's eBusiness Suite (EBS) account, where support reprentatives can see it.

You can also set the summary directly, by creating an account note whose subject begins with `Summary (cluster {cluster-ID}): ` and deleting any previous summary notes.
An example subject would be:

```
Summary (cluster 09d9436d-52bb-48ba-9026-2ab047158ef6): Cluster appears to have misconfigured ingress DNS
```

You can also [comment on the cluster](#comment-on-a-cluster) without updating the summary.

## Get the detailed support history for a cluster

When you want more detail than the current summary provides, ask the bot for all the details:

```
@cluster-support-bot detail 09d9436d-52bb-48ba-9026-2ab047158ef6
```

The bot will respond with the current cluster summary and any comments in reverse-chronological order.

## Comment on a cluster

When you want to add a comment about the cluster without updating the summary:

```
@cluster-support-bot comment 09d9436d-52bb-48ba-9026-2ab047158ef6
This is your subject, e.g. Opened support case about the missing *.apps DNS records
This is your body, e.g. Case https://example.com/123  Customer says they may be
able to dig into this tomorrow.
```

The bot will post the comment to the customer's eBusiness Suite (EBS) account, where support reprentatives can see it.

You can also add a comment directly, by creating an account note whose subject includes the cluster ID.
An example subject would be:

```
09d9436d-52bb-48ba-9026-2ab047158ef6 Opened support case about the missing *.apps DNS records
```
