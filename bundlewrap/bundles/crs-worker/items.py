from bundlewrap.exceptions import BundleError

assert node.has_bundle('encoder-common')

WORKER_SCRIPTS = {
    'recording-scheduler': {
        'secret': 'meta',
        'script': 'script-A-recording-scheduler.pl',
    },
    'mount4cut': {
        'secret': 'meta',
        'script': 'script-B-mount4cut.pl',
    },
    'cut-postprocessor': {
        'secret': 'meta',
        'script': 'script-C-cut-postprocessor.pl',
    },
    'postencoding': {
        'secret': 'meta',
        'script': 'script-E-postencoding-auphonic.pl',
    },
    'postprocessing': {
        'secret': 'meta',
        'script': 'script-F-postprocessing-upload.pl',
    },
    'autochecker': {
        'secret': 'autochecker',
        'script': 'script-X-checking-dummy.pl',
        'environment': {
            'CRS_ISMASTER': 'no',
        },
    }
}

number_of_workers = node.metadata.get('crs-worker/number_of_encoding_workers')
if number_of_workers > 1:
    for i in range(number_of_workers):
        WORKER_SCRIPTS[f'encoding{i}'] = {
            'secret': 'encoding',
            'script': 'script-D-encoding.pl',
        }
else:
    WORKER_SCRIPTS['encoding'] = {
        'secret': 'encoding',
        'script': 'script-D-encoding.pl',
    }

directories['/opt/crs-scripts'] = {}
git_deploy['/opt/crs-scripts'] = {
    'repo': 'https://github.com/crs-tools/crs-scripts.git',
    'rev': 'master',
}

# for HD-Master r22
directories['/usr/local/lib/ladspa'] = {}
files['/usr/local/lib/ladspa/master_me.so'] = {
    'mode': '0755',
    'after': {
        'pkg_apt:ffmpeg',
    },
    'content_type': 'binary',
}

if not node.has_bundle('cifs-client'):
    files['/video/upload-key'] = {
        'content_type': 'any', # do not touch file contents
        'owner': 'voc',
        'mode': '0600',
        'unless': '! test -f /video/upload-key',
    }

files['/etc/fuse.conf'] = {}

files['/usr/local/sbin/crs-mount'] = {
    'mode': '0700',
}

files['/usr/local/sbin/rsync-from-encoder'] = {
    'owner': 'voc',
    'mode': '0700',
}

files['/usr/local/lib/systemd/system/rsync-from-encoder@.service'] = {
    'content_type': 'mako',
    'context': {
        'slug': node.metadata.get('event/slug'),
    },
    'triggers': {
        'action:systemd-reload',
    },
}

files['/usr/local/sbin/rsync-to-storage'] = {
    'owner': 'voc',
    'mode': '0700',
}

files['/usr/local/lib/systemd/system/rsync-to-storage@.service'] = {
    'content_type': 'mako',
    'context': {
        'slug': node.metadata.get('event/slug'),
    },
    'triggers': {
        'action:systemd-reload',
    },
}

files['/usr/local/lib/systemd/system/crs-worker.target'] = {
    'triggers': {
        'action:systemd-reload',
    },
}

files['/usr/local/sbin/crs-status'] = {
    'content_type': 'mako',
    'context': {
        'scripts': WORKER_SCRIPTS,
    },
    'mode': '0755',
}

directories['/etc/crs-scripts'] = {
    'purge': True,
}

autostart_scripts = node.metadata.get('crs-worker/autostart_scripts', set())
for worker, config in WORKER_SCRIPTS.items():
    if config['secret'] not in node.metadata.get('crs-worker/secrets', {}):
        # no secrets for this worker type available, just ignore it then,
        # except if it was requested to auto-start.
        if worker in autostart_scripts:
            raise BundleError(f'{node.name} requested crs worker {worker} to auto-start, but secrets are missing')
        continue

    environment = {
        'CRS_TRACKER': node.metadata.get('crs-worker/tracker_url'),
        'CRS_TOKEN': node.metadata.get(f'crs-worker/secrets/{config["secret"]}/token'),
        'CRS_SECRET': node.metadata.get(f'crs-worker/secrets/{config["secret"]}/secret'),
        **config.get('environment', {})
    }

    if node.metadata.get('crs-worker/use_vaapi'):
        environment['CRS_USE_VAAPI'] = 'yes'

    if node.metadata.get('crs-worker/room_name', None):
        environment['CRS_ROOM'] = node.metadata.get('crs-worker/room_name')

    files[f'/etc/systemd/system/crs-{worker}.service'] = {
        'delete': True,
        'triggers': {
            'action:systemd-reload',
        },
    }

    files[f'/etc/crs-scripts/{config["secret"]}'] = {
        'content_type': 'mako',
        'source': 'crs-runner.env',
        'context': {
            'env': environment,
        },
        'triggers': set(), # see below
    }

    files[f'/usr/local/lib/systemd/system/crs-{worker}.service'] = {
        'content_type': 'mako',
        'source': 'crs-runner.service',
        'context': {
            'autostart': (worker in autostart_scripts),
            'script': config['script'],
            'secret': config['secret'],
            'worker': worker,
        },
        'triggers': {
            'action:systemd-reload',
            # When changing the 'Install' section of a unit file, the unit
            # needs to be disabled and then re-enabled to fix the symlinks.
            # Since we cannot know what exactly changed, we simply disable
            # the worker every time the unit file has been changed.
            # Bundlewrap will re-enable it afterwards.
            f'action:crs-worker_disable_worker_{worker}',
        },
    }

    actions[f'crs-worker_disable_worker_{worker}'] = {
        'command': f'systemctl disable crs-{worker}',
        'triggered': True,
        'before': {
            f'svc_systemd:crs-{worker}',
        },
    }

    if worker in autostart_scripts:
        files[f'/usr/local/lib/systemd/system/crs-{worker}.service']['triggers'].add(
            f'svc_systemd:crs-{worker}:restart',
        )
        files[f'/etc/crs-worker/{config["secret"]}']['triggers'].add(
            f'svc_systemd:crs-{worker}:restart',
        )

    svc_systemd[f'crs-{worker}'] = {
        # do not start these workers automatically, unless requested
        'running': (True if worker in autostart_scripts else None),
        'needs': {
            f'file:/etc/crs-scripts/{config["secret"]}',
            f'file:/usr/local/lib/systemd/system/crs-{worker}.service',
            'git_deploy:/opt/crs-scripts',
        },
    }

# delete legacy stuff
files['/opt/tracker-profile.sh'] = {'delete': True}
files['/opt/tracker-profile-meta.sh'] = {'delete': True}
files['/opt/crs-scripts/tracker-profile.sh'] = {'delete': True}
files['/opt/crs-scripts/tracker-profile-meta.sh'] = {'delete': True}
