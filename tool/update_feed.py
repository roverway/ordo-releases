#!/usr/bin/env python3
"""Build immutable release metadata and the public Pages feed, using stdlib only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
ASSET = re.compile(
    r"^ordo-(?:.+-)?(android|linux|windows)-(arm64-v8a|armeabi-v7a|x86_64|universal|aarch64|x64)\.(apk|AppImage|zip)$"
)


def version_key(version):
    match = SEMVER.fullmatch(version)
    if not match:
        raise ValueError(f"Invalid SemVer: {version}")
    pre = match[4]
    parts = []
    for part in pre.split('.') if pre else []:
        if part.isdigit() and len(part) > 1 and part.startswith('0'):
            raise ValueError(f"Invalid SemVer identifier: {part}")
        parts.append((0, int(part)) if part.isdigit() else (1, part))
    return (int(match[1]), int(match[2]), int(match[3]), pre is None, tuple(parts))


def asset_record(name, size, digest, url):
    match = ASSET.fullmatch(name)
    if not match or not re.fullmatch(r"[0-9a-f]{64}", digest or '') or size <= 0:
        raise ValueError(f"Invalid package metadata: {name}")
    return {
        'name': name, 'platform': match[1], 'arch': match[2],
        'size': size, 'sha256': digest,
        'sources': [{'id': 'GitHub', 'url': url}],
    }


def release_manifest(directory, repository, version, build_number, certificate):
    key = version_key(version)
    assets = []
    base = f'https://github.com/{repository}/releases/download/{quote("v" + version, safe="")}'
    for path in sorted(Path(directory).iterdir()):
        if path.is_file() and ASSET.fullmatch(path.name):
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            assets.append(asset_record(path.name, path.stat().st_size, digest,
                                       f'{base}/{quote(path.name)}'))
    if not assets:
        raise ValueError('No release packages found')
    return {
        'schemaVersion': 1, 'channel': 'stable' if key[3] else 'beta',
        'version': version, 'buildNumber': build_number,
        'androidCertificateSha256': certificate,
        'assets': assets,
    }


def api_json(url, token):
    request = Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'User-Agent': 'ordo-update-feed',
    })
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def list_releases(repository, token):
    releases = []
    page = 1
    while True:
        batch = api_json(f'https://api.github.com/repos/{repository}/releases?per_page=100&page={page}', token)
        releases.extend(batch)
        if len(batch) < 100:
            return releases
        page += 1


def select_releases(releases):
    selected = {'stable': None, 'beta': None}
    for release in releases:
        if release['draft']:
            continue
        version = release['tag_name'].removeprefix('v')
        try:
            key = version_key(version)
        except ValueError:
            continue
        channel = 'beta' if release['prerelease'] else 'stable'
        if (channel == 'stable') != key[3]:
            continue
        # Incomplete or source-only releases must not hide usable packages.
        packages = [a for a in release['assets'] if ASSET.fullmatch(a['name'])]
        if not packages:
            continue
        current = selected[channel]
        if current is None or key > version_key(current['tag_name'].removeprefix('v')):
            selected[channel] = release
    return selected


def pages_feed(repository, token, releases=None):
    selected = select_releases(releases if releases is not None else list_releases(repository, token))
    channels = {}
    for channel, release in selected.items():
        if release is None:
            channels[channel] = None
            continue
        version = release['tag_name'].removeprefix('v')
        assets = []
        for asset in release['assets']:
            if ASSET.fullmatch(asset['name']):
                digest = (asset.get('digest') or '').removeprefix('sha256:')
                assets.append(asset_record(asset['name'], asset['size'], digest,
                                           asset['browser_download_url']))
        metadata_asset = next((a for a in release['assets'] if a['name'] == 'update-manifest.json'), None)
        metadata = None
        if metadata_asset:
            # Public URL only: never send the API token to asset/CDN redirects.
            with urlopen(metadata_asset['browser_download_url'], timeout=30) as response:
                metadata = json.load(response)
            if metadata['schemaVersion'] != 1 or metadata['version'] != version or metadata['channel'] != channel:
                raise ValueError('Release metadata does not match its tag')
            by_name = {a['name']: a for a in metadata['assets']}
            for asset in assets:
                original = by_name[asset['name']]
                if asset['sha256'] != original['sha256'] or asset['size'] != original['size']:
                    raise ValueError(f'Package changed after metadata generation: {asset["name"]}')
                if 'androidVersionCode' in original:
                    code = original['androidVersionCode']
                    if asset['platform'] != 'android' or type(code) is not int or code <= 0:
                        raise ValueError('Invalid Android package version code')
                    asset['androidVersionCode'] = code
        channels[channel] = {
            'version': version, 'buildNumber': metadata['buildNumber'] if metadata else None,
            'releaseUrl': release['html_url'], 'notes': release.get('body') or '',
            'publishedAt': release['published_at'],
            'androidCertificateSha256': metadata.get('androidCertificateSha256') if metadata else None,
            'assets': assets,
        }
    return {'schemaVersion': 1, 'channels': channels}


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    release = commands.add_parser('release')
    release.add_argument('--directory', required=True)
    release.add_argument('--repository', required=True)
    release.add_argument('--version', required=True)
    release.add_argument('--build-number', type=int, required=True)
    release.add_argument('--certificate', required=True)
    release.add_argument('--output', required=True)
    pages = commands.add_parser('pages')
    pages.add_argument('--repository', required=True)
    pages.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'release':
        data = release_manifest(args.directory, args.repository, args.version,
                                args.build_number, args.certificate)
    else:
        data = pages_feed(args.repository, os.environ['GH_TOKEN'])
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
