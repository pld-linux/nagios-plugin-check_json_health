#!/usr/bin/python3
#
# This work is dedicated to the public domain under CC0 1.0.
# https://creativecommons.org/publicdomain/zero/1.0/
#
# To the extent possible under law, the author(s) have dedicated all
# copyright and related and neighboring rights to this software to the
# public domain worldwide. This software is distributed without any warranty.
#
"""
check_json_health - Generic Nagios plugin for JSON health endpoints.

Checks any HTTP(S) URL that returns JSON with standard health fields:
  - exit_code: Nagios exit code (0=OK, 1=WARNING, 2=CRITICAL, 3=UNKNOWN)
  - status:    Status keyword (OK, WARNING, CRITICAL, UNKNOWN)
  - message:   Human-readable status message

The server owns all threshold logic. This plugin simply fetches,
extracts, and forwards the status to Nagios.

Dependencies: Python 3 stdlib only (no pip packages).

Installation:
  cp check_json_health /usr/lib/nagios/plugins/
  chmod +x /usr/lib/nagios/plugins/check_json_health

Usage:
  check_json_health -H <hostname> [-p <port>] [-u <uri>] [-t <timeout>]
  check_json_health -H k-gw-prod.example.com -u /nagios/ --perfdata-field details
  check_json_health -H myapp.example.com -u /health -k --no-ssl -p 8080
"""

import argparse
import json
import ssl
import sys
import urllib.request

OK, WARNING, CRITICAL, UNKNOWN = 0, 1, 2, 3


def sanitize(s):
    """Remove characters that could break Nagios output parsing.

    Strips pipe (perfdata separator), newlines (Nagios reads first line only),
    and carriage returns from values originating in the JSON response.
    """
    return str(s).replace('|', '/').replace('\n', ' ').replace('\r', '')


def main():
    parser = argparse.ArgumentParser(
        description='Nagios plugin: check a JSON health endpoint')
    parser.add_argument('-H', '--hostname', required=True,
                        help='Server hostname or IP')
    parser.add_argument('-p', '--port', type=int, default=443,
                        help='Port (default: 443)')
    parser.add_argument('-u', '--uri', default='/nagios/',
                        help='URI path (default: /nagios/)')
    parser.add_argument('--no-ssl', action='store_true', default=False,
                        help='Use plain HTTP instead of HTTPS (default: HTTPS)')
    parser.add_argument('-k', '--insecure', action='store_true',
                        help='Skip SSL certificate verification')
    parser.add_argument('-t', '--timeout', type=int, default=15,
                        help='Connection timeout in seconds (default: 15)')
    parser.add_argument('--status-field', default='status',
                        help='JSON field for status keyword (default: status)')
    parser.add_argument('--exit-code-field', default='exit_code',
                        help='JSON field for exit code (default: exit_code)')
    parser.add_argument('--message-field', default='message',
                        help='JSON field for message (default: message)')
    parser.add_argument('--perfdata-field', default=None,
                        help='JSON field for perfdata - dict of key:number '
                             'or pre-formatted string (default: none)')
    args = parser.parse_args()

    scheme = 'http' if args.no_ssl else 'https'
    url = f'{scheme}://{args.hostname}:{args.port}{args.uri}'

    try:
        if args.no_ssl:
            ctx = None
        else:
            ctx = ssl.create_default_context()
            if args.insecure:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers={'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=args.timeout, context=ctx) as resp:
            body = resp.read().decode('utf-8')
    except Exception as e:
        # Connectivity/infrastructure failure = UNKNOWN (service state is indeterminate)
        print(f'UNKNOWN - {url}: {e}')
        sys.exit(UNKNOWN)

    try:
        data = json.loads(body)

        exit_code = int(data.get(args.exit_code_field, UNKNOWN))
        if exit_code not in (OK, WARNING, CRITICAL, UNKNOWN):
            exit_code = UNKNOWN

        status = sanitize(data.get(args.status_field, 'UNKNOWN'))
        message = sanitize(data.get(args.message_field, 'No message in response'))

        output = f'{status} - {message}'

        # Optional perfdata from a JSON field
        if args.perfdata_field:
            perfdata_raw = data.get(args.perfdata_field)
            if isinstance(perfdata_raw, dict):
                pairs = ' '.join(
                    f'{sanitize(k)}={v}'
                    for k, v in perfdata_raw.items()
                    if isinstance(v, (int, float))
                )
                if pairs:
                    output += f' | {pairs}'
            elif isinstance(perfdata_raw, str) and perfdata_raw:
                output += f' | {sanitize(perfdata_raw)}'

        print(output)
        sys.exit(exit_code)
    except Exception as e:
        # JSON parse or field extraction failure = CRITICAL (service returned garbage)
        print(f'CRITICAL - {url}: {e}')
        sys.exit(CRITICAL)


if __name__ == '__main__':
    main()
