from bundlewrap.metadata import atomic

defaults = {
    'apt': {
        'packages': {
            'decklink-debugger': {},
            'desktopvideo': {},
            'desktopvideo-gui': {},
            'fbset': {},
            'gstreamer1.0-libav': {},
            'xauth': {}, # for x11 forwarding
        },
    },
    'voctocore': {
        'mirror_view': False, # automatically mirrors SBS/LEC views
        'parallel_slide_recording': True,
        'parallel_slide_streaming': True,
        'static_background_image': True,
        'streaming_use_dynaudnorm': False,
        'vaapi': False,
        'srt_publish': True,
        'backgrounds': {
            'lec': {
                'kind': 'img',
                'path': '/opt/voc/share/bg_lec.png',
                'composites': 'lec',
            },
            'lecm': {
                'kind': 'img',
                'path': '/opt/voc/share/bg_lecm.png',
                'composites': '|lec',
            },
            'sbs': {
                'kind': 'img',
                'path': '/opt/voc/share/bg_sbs.png',
                'composites': 'sbs',
            },
            'fs': {
                'kind': 'test',
                'pattern': 'black',
                'composites': 'fs',
            },
        },
    },
}

if not node.has_bundle('zfs'):
    defaults['mqtt-monitoring'] = {
        'plugins_daily': {
            'disk_space_usage',
        },
    }

@metadata_reactor.provides(
    'voctocore/sources',
)
def auto_audio_level(metadata):
    sources = {}
    for aname, aconfig in metadata.get('voctocore/audio', {}).items():
        sources[aconfig['input']] = {
            'volume': aconfig.get('volume', '1.0'),
        }

    return {
        'voctocore': {
            'sources': sources,
        },
    }


@metadata_reactor.provides(
    'firewall/port_rules',
)
def firewall(metadata):
    port_rules = {}

    for port in (
        9998,
        9999,
        11000, # mix recording
        11100, # mix preview
        12000,
        14000,
        15000, # mix live
        15100, # mix preview live
        16000, # background video
        17000, # video blinder
        18000, # audio blinder
    ):
        port_rules[str(port)] = atomic(metadata.get('voctocore/restrict-to', set()))


    for idx, source in enumerate(metadata.get('voctocore/sources', {})):
        for port in (
            10000, # source input
            13000, # source recording
            13100, # source preview
            15001, # source live
        ):
            port_rules[str(port+idx)] = atomic(metadata.get('voctocore/restrict-to', set()))


    return {
        'firewall': {
            'port_rules': port_rules,
        },
    }
