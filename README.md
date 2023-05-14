# Slack Autoarchive
## What?
The idea was stolen from https://github.com/Symantec/slack-autoarchive.
That script no longer works because some API calls it uses were deprecated.
This version goes through a Slack instance and automatically archives all unused channels based on channel history.

## Why?
I used this as a learning opportunity. Initially I used the Symantec script at my workplace and simply swapped out the deprecated API calls.
But the more I used it the more ideas for improvement I had. I chose to not let scope creep get the best of me for my work project, but thought it would be fun to go all out writing this from scratch on my own time, so here we are.

This is the first script I'm making public and the first time I'm trying to use good documentation.
As one of the main goals of this is learning, suggestions for improvement are welcome.

Note that it currently doesn't use Docker, but I plan to integrate that as I learn more about it.

## How?
The script has a dry run mode where it simply gathers a list of channels that would be archived. In a true run, the channels are actually archived.

A channel is considered inactive if it:
- Is older than the amount of days specified in `config.py`.
- Has a message that is not of a subtype defined in `config.py`.
- Is not marked exempt via `config.py`.
- Does not contain the exemption string defined in `config.py` in the channel topic.
- Does not contain more than the minimum members defined in `config.py`.
- Has a message that is older than the amount of days specified in `config.py`.

In both dry and true runs, a csv file is generated with the results and sent as an admin report to the specified channel.

## Differences
- This script is able to automatically join channels.
  - This is a prerequisite before the bot can really do anything.
- A list of channel users is gathered and noted before archiving.
  - If a channel ever needs to be unarchived, users may need to be added back manually.
- Function type hints are used.
- The original script looked at non-bot messages, but this scripts treats bot messages as regular messages.
  - It instead skips certain messages based on certain message subtype.

## Usage
### Prerequisites
- python3
- Install requirements.txt ( `pip install -r requirements.txt` )
- [Slack OAuth token](https://api.slack.com/docs/oauth) with these permissions:
  - `channels:history`
  - `channels:join`
  - `channels:manage`
  - `channels:read`
  - `chat:write`
  - `files:read`
  - `files:write`
  - `im:history`
  - `im:read`
  - `mpim:history`
  - `mpim:read`
  - `users:read`
  - `chat:write:bot`
  - `chat:write:user`