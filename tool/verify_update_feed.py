#!/usr/bin/env python3
"""Verify the anonymous update URL after deployment; a green Pages job is not enough."""
import argparse
import json
from pathlib import Path
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

try:
    from .update_feed import version_key
except ImportError:
    from update_feed import version_key


def verify_feed(url, expected=None, version=None, attempts=12, interval=10,
                opener=urlopen, sleeper=time.sleep):
    if expected is None and version is None:
        raise ValueError('Expected feed or version is required')
    if attempts < 1 or interval < 0:
        raise ValueError('Invalid retry settings')
    channel = ('stable' if version_key(version)[3] else 'beta') if version else None
    last_error = None
    for attempt in range(attempts):
        parts = urlsplit(url)
        query = parse_qsl(parts.query, keep_blank_values=True)
        query.append(('deployment_check', str(time.time_ns())))
        request_url = urlunsplit(parts._replace(query=urlencode(query)))
        request = Request(request_url, headers={
            'Cache-Control': 'no-cache, no-store',
            'Pragma': 'no-cache',
            'User-Agent': 'ordo-update-feed-verifier',
        })
        try:
            with opener(request, timeout=15) as response:
                live = json.load(response)
            if expected is not None and live != expected:
                versions = {k: (v or {}).get('version')
                            for k, v in live.get('channels', {}).items()}
                raise ValueError(f'Served feed differs from deployment: {versions}')
            if version is not None:
                release = live.get('channels', {}).get(channel) or {}
                current = release.get('version', '')
                if (version_key(current) < version_key(version)
                        or not release.get('assets')):
                    raise ValueError(f'Expected {channel} >= {version}, served {current}')
            print('Verified public feed:', {
                k: (v or {}).get('version') for k, v in live['channels'].items()
            })
            return live
        except Exception as error:
            last_error = error
            print(f'Feed verification {attempt + 1}/{attempts}: {error}', flush=True)
        if attempt + 1 < attempts:
            sleeper(interval)
    raise RuntimeError(f'Public update feed did not update: {last_error}') from last_error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--expected-file', type=Path)
    parser.add_argument('--version')
    parser.add_argument('--attempts', type=int, default=12)
    parser.add_argument('--interval', type=float, default=10)
    args = parser.parse_args()
    expected = json.loads(args.expected_file.read_text()) if args.expected_file else None
    verify_feed(args.url, expected, args.version, args.attempts, args.interval)


if __name__ == '__main__':
    main()
