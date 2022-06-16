assert node.has_bundle('encoder-common')

directories['/opt/crs-scripts'] = {}

git_deploy['/opt/crs-scripts'] = {
    'repo': 'https://github.com/crs-tools/crs-scripts.git',
    'rev': 'master',
}

files['/opt/crs-scripts/tracker-profile.sh'] = {
    'content_type': 'mako',
    'source': 'environment',
    'context': {
        'url': node.metadata.get('crs-worker/tracker_url'),
        'vaapi': node.metadata.get('crs-worker/use_vaapi'),
        'token': node.metadata.get('crs-worker/token/encoding'),
        'secret': node.metadata.get('crs-worker/secret/encoding'),
    },
}
files['/opt/crs-scripts/tracker-profile-meta.sh'] = {
    'content_type': 'mako',
    'source': 'environment',
    'context': {
        'url': node.metadata.get('crs-worker/tracker_url'),
        'vaapi': node.metadata.get('crs-worker/use_vaapi'),
        'token': node.metadata.get('crs-worker/token/meta', node.metadata.get('crs-worker/token/encoding')),
        'secret': node.metadata.get('crs-worker/secret/meta', node.metadata.get('crs-worker/secret/encoding')),
    },
}

for worker, script in {
    'recording-scheduler': 'script-A-recording-scheduler.pl',
    'mount4cut': 'script-B-mount4cut.pl',
    'cut-postprocessor': 'script-C-cut-postprocessor.pl',
    'encoding': 'script-D-encoding.pl',
    'postencoding': 'script-E-postencoding-auphonic.pl',
    'postprocessing': 'script-F-postprocessing-upload.pl',
}.items():
    files[f'/etc/systemd/system/crs-{worker}.service'] = {
        'content_type': 'mako',
        'source': 'crs-runner.service',
        'context': {
            'worker': worker,
            'script': script,
        },
        'triggers': {
            'action:systemd-reload',
        },
    }
