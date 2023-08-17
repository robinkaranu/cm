from bundlewrap.exceptions import BundleError

event = node.metadata.get('event/slug')

directories[f'/video'] = {
    'owner': 'voc',
    'group': 'voc',
}

for path in (
    'capture',
    'encoded',
    'fuse',
    'intros',
    'tmp',
):
    directories[f'/video/{path}'] = {
        'owner': 'voc',
        'group': 'voc',
    }

    directories[f'/video/{path}/{event}'] = {
        'before': {
            'bundle:voctocore',
            'bundle:crs-worker',
        },
        'owner': 'voc',
        'group': 'voc',
    }

directories[f'/video/tmp/{event}/repair'] = {
    'before': {
        'bundle:voctocore',
        'bundle:crs-worker',
    },
    'owner': 'voc',
    'group': 'voc',
}
