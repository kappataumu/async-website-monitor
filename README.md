# Async Website Monitor
A minimal yet functional website uptime and monitoring tool written in Python, using [asyncio](https://docs.python.org/3/library/asyncio.html) and [aiohttp](https://github.com/KeepSafe/aiohttp) for maximum speed. When one of your URLs errors out, an e-mail alert will be delivered to your inbox by [MailGun](https://www.mailgun.com/).

## Installation

```
git clone https://github.com/kappataumu/async-website-monitor
pip install -r async-website-monitor/requirements.txt
```


## Features
* Supports any HTTP verb (POST, GET, PUT, PATCH, DELETE)
* Can check for custom HTTP status codes
* Finds text in the parsed HTML
* Finds any string in the raw response text (useful for finding stuff in HTML source code or JSON responses)
* E-mail notifications when checks fail
* Configurable e-mail reports even when no errors are found


## Requirements
* Python 3.5.1 or newer
* Beautiful Soup 4
* requests
* MailGun (optional)


## Configuration

A number of settings are available, which are required if you want to use the e-mail reporting functionality. All of them should be set:

| Setting | Description
| --- | ---|
| MAILGUN_TO | E-mail address: Where e-mail reports will be sent. |
| MAILGUN_FROM | E-mail address: From where the e-mails will appear to originate.  |
| MAILGUN_API_KEY | Your MailGun API key. |
| MAILGUN_DOMAIN | Your MailGun custom domain. |
| HEARTBEAT_EVERY | Send a report every this amount of seconds, even if no checks failed. |
| USE_MAILGUN | Either `true` or `false`. Set to enable e-mail sending. All the other settings should be set as well. |

These are expected to be found in `./config.json`, but you can specify a custom file on the command line as well:

`asymo.py --config=/path/to/my/file/config.json`

The default `config.json` is shown below:

```json
{
    "MAILGUN_TO" : "",
    "MAILGUN_FROM" : "",
    "MAILGUN_API_KEY" : "",
    "MAILGUN_CUSTOM_DOMAIN" : "",
    "HEARTBEAT_EVERY" : 86400,
    "USE_MAILGUN": false
}
```

Environment variables are supported as well, and take precedence if found:

```bash
export MAILGUN_TO="user@example.com",
export MAILGUN_FROM="devops@example.com",
export MAILGUN_API_KEY="key-ppxxffffd1dceddddda4daaaaaaaaaaa",
export MAILGUN_CUSTOM_DOMAIN="ops.example.com"
export HEARTBEAT_EVERY="86400"
export USE_MAILGUN=""
```


## Setting up checks

The URLs you want to monitor along with any explicit checks should be placed in `./watchlist.json`, but you can specify a custom file on the command line as well:

`asymo.py --watchlist=/path/to/my/file/watchlist.json`

In order to keep configuration to a minimum, if you are happy with a `GET` request being issued and a `200` status code check, you only need to provide the URL to be checked, like so:

```json
{
    "http://kappataumu.com": {},
    "https://github.com/kappataumu?tab=activity": {}
}
```

A number of optional checks can be specified, for more advanced monitoring. You can mix and match these as you see fit:


| Parameter | Description |
| --------- | ----------- |
| "method" | The HTTP method to use (one of POST, GET, PUT, PATCH, DELETE) |
| "status" | The expected status code |
| "text_in_html" | Parses the HTML and then searches for the given string |
| "text_in_raw" | Searches for the given string in the raw response (useful for finding strings in HTML source code or JSON responses) |



Here is a hypothetical `hosts.json` with a couple of more advanced examples based on the above:

```json
{
    "http://kappataumu.com": {
        "text_in_html": "About me",
        "text_in_raw": "twitter:image"
    },
    "http://google.com": {
        "status": 302
    },
    "https://api.github.com/zen": {
        "status": 200
    },
    "http://swapi.co/api/planets/3/" : {
        "text_in_raw": "Yavin IV"
    }
}
```
