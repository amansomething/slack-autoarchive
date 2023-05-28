# Slack Autoarchive
## What?
This was inspired by https://github.com/Symantec/slack-autoarchive.
That script no longer works because some API calls it uses were deprecated.
This version goes through a Slack instance and automatically archives all unused channels based on channel history.

## Why?
I used this as a learning opportunity. Initially I used the Symantec script at my workplace and simply swapped out the deprecated API calls.
But the more I used it the more ideas for improvement I had. I chose to not let scope creep get the best of me for my work project, but thought it would be fun to go all out writing this from scratch on my own time, so here we are.

This is the first script I'm making public and the first time I'm trying to use good documentation.
One of my main goals of this project is to learn. Suggestions for improvement are welcome.
This is also a chance for me to learn how to use git better.

## How?
The script has a dry run mode where it simply gathers a list of channels that would be archived. In a true run, the channels are actually archived.

A channel is considered inactive if it:
- Is older than the amount of days specified in `config.py`.
- Has a message that is not of a subtype defined in `config.py`.
- Has a message that is older than the amount of days specified in `config.py`.
- Is not marked exempt via `config.py`.
- Does not contain the exemption string defined in `config.py` in the channel topic.
- Does not contain more than the minimum members defined in `config.py`.

In both dry and true runs, a csv file is generated with the results and sent as an admin report to the specified channel.

## Differences From Symantec Script
- This script is able to automatically join channels.
  - This is a prerequisite before the bot can really do anything.
- A list of channel users is gathered and noted before archiving.
  - If a channel ever needs to be unarchived, users may need to be added back manually.
- Function type hints are used.
- The original script looked at non-bot messages, but this scripts treats bot messages as regular messages.
  - It instead skips certain messages based on message subtypes.

## Usage
### Prerequisites
- `python3` must be installed if running without Docker.
- Docker must be installed if running with Docker.
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
- Set the token as an environmental variable:
  - macOS and Linux: `export API_TOKEN={ACTUAL TOKEN HERE}`
  - Windows: <https://chlee.co/how-to-setup-environment-variables-for-windows-mac-and-linux/>

### Adjust config.py as Needed
The variables here can be adjusted before creating the docker image.
Alternatively, send as env vars when running the container.

| Variable                         | Notes                                                                                                                   |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| **DRY_RUN**                      | Does not archive channels if True.                                                                                      |
| **MIN_MEMBERS**                  | If set to 0, does nothing. Otherwise, any channel with more  people than this is exempt from being archived.            |
| **DAYS_INACTIVE**                | How many days old does the last message in a channel have to be to be considered inactive?                              |
| **DEFAULT_NOTIFICATION_CHANNEL** | Where to send the admin report. Default=general. The '#' is optional.                                                   |
| **JOIN_CHANNELS**                | If set to True, attempts to join all channels. This is not needed every time the script is run when testing/developing. |
| **RESULTS_FILE**                 | Name of the csv file to write out the results to. This file is sent to DEFAULT_NOTIFICATION_CHANNEL.                    |
| **EXEMPT_SUBTYPES_RAW**          | Any channel message subtypes to ignore. See [Message API Reference](https://api.slack.com/events/message) for details.  |
| **ALLOWLIST_KEYWORDS_RAW**       | Any words in this list that show up in a channel's topic will allow the channel to be exempt from being archived.       |
| **EXEMPT_CHANNELS_RAW**          | Any channel names that should be exempt from being archived.                                                            |

### Run Script - Without Docker
- Install requirements.txt
  - `pip install -r requirements.txt`
- Open a shell in the same directory as the script files and run:
  - `python3 main.py`

### Run Script - With Docker
- Build the image:
  - `docker image build . -t autoarchive`
- Run container as a dry run:
```
docker container run -it \
-e API_TOKEN=$API_TOKEN \
-t autoarchive
```
- Run container in production mode:
```
docker container run -it \
-e API_TOKEN=$API_TOKEN \
-e DRY_RUN=False \
-t autoarchive
```
Additional variables can be passed along using the format `-e VAR=VAL`.

### Improvement Ideas
- ~~Dockerize it~~ Done!
  - Use .env file for vars
  - Use docker-compose
- ~~Have more variables be set as env vars~~ Done!
- Have a local cache of channel info.
  - Not particularly useful when running in production, but nice to make fewer API calls when testing.
- Not too experienced with making Object-Oriented scripts, but seems like that's worth trying out.
- Make a GUI?