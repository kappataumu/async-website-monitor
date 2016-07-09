#!/usr/bin/env python

import aiohttp
import argparse
import asyncio
import json
import logging
import os
import time

from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("--config")
parser.add_argument("--watchlist")
args = parser.parse_args()

# Absolute paths are better than relative
absolute = os.path.dirname(os.path.abspath(__file__))
files = {
    'report.log'  : absolute + '/logs/report.log',
    'asymo.log'     : absolute + '/logs/asymo.log',
    'watchlist.json' : args.watchlist if args.watchlist else absolute + '/watchlist.json',
    'config.json' : args.config if args.config else absolute + '/config.json',
    '.heartbeat'  : absolute + '/.heartbeat',
}

# Only these options will be picked up fron config.json
options = (
    'MAILGUN_TO',
    'MAILGUN_FROM',
    'MAILGUN_API_KEY',
    'MAILGUN_DOMAIN',
    'USE_MAILGUN',
    'HEARTBEAT_EVERY',
    'ALLOW_REDIRECTS',
)

# asymo.log accumulates output from every run
# report.log stores the output of the most recent run
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler(files['report.log'], 'w'))
logger.addHandler(logging.FileHandler(files['asymo.log']))
logger.setLevel(logging.INFO)

t = time.monotonic()
logger.info("Work started: {0}\n".format(time.strftime("%Y/%m/%d %H:%M:%S")))

try:
    watchlist  = json.loads(open(files['watchlist.json']).read())
    config_js = json.loads(open(files['config.json']).read())
except Exception:
    logger.critical((
        "Ensure the following files are are present and valid JSON:\n"
        "Settings: {0}\n"
        "Watchlist: {1}"
        .format(files['config.json'], files['watchlist.json'])
    ))
    exit()

config = {}
for option in options:
    config[option] = os.environ.get(option, config_js.get(option))

if config['USE_MAILGUN']:
    mgopt = ('MAILGUN_TO', 'MAILGUN_FROM', 'MAILGUN_API_KEY', 'MAILGUN_DOMAIN')
    if not all([config[m] for m in mgopt]):
        config['USE_MAILGUN'] = False
        logger.warning("Unable to configure MailGun. E-mails won't be sent.\n")
        

def email(report):
    url = (
        'https://api.mailgun.net/v3/{0}/messages'
        .format(config['MAILGUN_DOMAIN'])
    )
    data = {
        'from': config['MAILGUN_FROM'],
        'to': config['MAILGUN_TO'],
        'subject': 'Async Website Monitor',
        'text': "Status report: \n" + report
    }
    
    
async def work(session, url, url_checks):
    
    method       = url_checks.get('method', 'GET')
    status       = url_checks.get('status', 200)
    text_in_html = url_checks.get('text_in_html')
    text_in_raw  = url_checks.get('text_in_raw')
    
    headers = {
        'user-agent': (
            'Mozilla/5.0 (Windows NT 6.3; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/52.0.2743.60 Safari/537.36'
        )
    }
    
    try:
        async with session.request(
            method,
            url,
            allow_redirects=config['ALLOW_REDIRECTS'],
            headers=headers
        ) as resp:
            
            if resp.status != status:
                logger.error((
                    "[ERROR] {0} => "
                    "Status code mismatch. "
                    "Got {1} instead of {2}".format(url, resp.status, status)
                ))
            else:
                logger.info(
                    "[OK] {0} => Status code: '{1}'".format(url, status)
                )
                
                source = await resp.text()
                
                if text_in_html:
                    soup = BeautifulSoup(source, 'html.parser')
                    if soup.find_all(string=text_in_html):
                        logger.info((
                            "[OK] {0} => "
                            "Text in HTML "
                            "not found: '{1}'".format(url, text_in_html)
                        ))
                    else:
                        logger.error((
                            "[ERROR] {0} => "
                            "Text in HTML "
                            "found: '{1}')".format(url, text_in_html)
                        ))
                
                if text_in_raw:
                    if text_in_raw in source:
                        logger.info((
                            "[OK] {0} => "
                            "String found: '{1}'".format(url, text_in_raw)
                        ))
                    else:
                        logger.error((
                            "[ERROR] {0} => "
                            "String not found: '{1}'".format(url, text_in_raw)
                        ))
                            
    except Exception as e:
        logger.error("Error: " + str(e))
    

async def dispatcher(session, watchlist, loop):
    futures = [
        loop.create_task(work(session, url, url_checks))
        for url, url_checks
        in watchlist.items()
    ]
    for future in asyncio.as_completed(futures):
        await future


def main():

    loop = asyncio.get_event_loop()
    conn = aiohttp.TCPConnector(verify_ssl=False)
    with aiohttp.ClientSession(loop=loop, connector=conn) as session:
        loop.run_until_complete(dispatcher(session, watchlist, loop))
    loop.close()
    
    e = str(time.monotonic() - t)
    logger.info("\nChecked {0} hosts in {1}s.".format(len(watchlist), e))

    if config['USE_MAILGUN']:
        report = open(files['report.log']).read()
        
        if '[ERROR]' in report:
            logger.info("E-mailing error report to " + config['MAILGUN_TO'])
            email(report)
        else:
            if config['HEARTBEAT_EVERY']:
                fh = open(files['.heartbeat'], 'r+')
                now = int(time.time())
                elapsed = now - int(fh.read())
                if elapsed > config['HEARTBEAT_EVERY']:
                    fh.seek(0)
                    fh.write(str(now))
                    fh.truncate()
                    logger.info("It's been a while, " + config['MAILGUN_TO'])
                    email(report)
                fh.close()

if __name__ == '__main__':
    main()
