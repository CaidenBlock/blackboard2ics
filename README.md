# Blackboard2ICS

A hacked together Python project for managing and syncing an improved Blackboard calendar.

## Features

- OAuth support for Microsoft SAML w/ 2FA via selenium, since Blackboard does not have a user API
- Pushes to a gist, for syncing across
- Output calendar can be easily customized, to see what options are available check [the ical docs](https://allenporter.github.io/ical/ical/event.html) 

## Setup and Usage

This uses uv, but it shouldn't need it
- pip install uv
- uv pip install -r pyproject.toml
- Create a private [GitHub gist](https://gist.github.com/)
- Create a [fine-grained access token](https://github.com/settings/personal-access-tokens/new)
- Create secrets.json (see example_secrets.json), this is a plaintext file an should not be stored on an unsecure or public device.
- uv run main.py
- create a cron job to run on a timer or when the regular ics updates

## Notice

- This code is largely AI-generated; this is a personal tool to achieve a desired result, not a learning project.

## License

MIT i guess