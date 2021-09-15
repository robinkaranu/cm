#!/usr/bin/env python3

import os
import time
import contextlib

import fanout_utils


def fanout_dash(context):
	context += {
		"starttime": int(time.time()),
	}

	cleanup(context)
	prepare(context)
	context += calculate_adaptation_sets(context)

	try:
		fanout(context)
	except fanout_utils.ExitException:
		print("Cleaning up")
		cleanup(context)
		raise

	cleanup(context)

def prepare(c):
	with contextlib.suppress(FileExistsError):
		os.mkdir(os.path.join(c.dash_write_path, c.stream))

def cleanup(c):
	with contextlib.suppress(FileNotFoundError):
		fanout_utils.remove_glob(os.path.join(
			c.dash_write_path, "%s/manifest.mpd" % c.stream))
		fanout_utils.remove_glob(os.path.join(
			c.dash_write_path, "%s/*.webm" % c.stream))
		fanout_utils.remove_glob(os.path.join(
			c.dash_write_path, "%s/*.webm.tmp" % c.stream))

	with contextlib.suppress(OSError):
		os.rmdir(os.path.join(c.dash_write_path, c.stream))


def calculate_adaptation_sets(c):
	first_audio_stream_index = len(c.video_tracks)
	set_id = 0

	# Video Tracks
	sets = [f"id={set_id},streams=v"]
	set_id += 1

	# Native
	sets += [f"id={set_id},streams={first_audio_stream_index+0}"]
	set_id += 1

	if 'Translated' in c.audio_tracks:
			# Translated
			sets += [f"id={set_id},streams={first_audio_stream_index+1}"]
			set_id += 1

	if 'Translated-2' in c.audio_tracks:
			# Translated-2
			sets += [f"id={set_id},streams={first_audio_stream_index+2}"]
			set_id += 1

	return {
		"adaptation_sets": sets,
		"first_audio_stream_index": first_audio_stream_index,
	}


def fanout(c):
	command = fanout_utils.format_and_strip(c, """
ffmpeg -v warning -nostats -nostdin -y -analyzeduration 50000000
	-i {{ pull_url }}

	-c:a copy
	-c:v copy

	-map 0:v:0 -b:v:0 2800k
{% if 'SD' in video_tracks %}
	-map 0:v:1 -b:v:1 800k
{% endif %}
{% if 'Slides' in video_tracks %}
	-map 0:v:2 -b:v:2 100k
{% endif %}

	-map 0:a:0 -b:a:0 96k -metadata:s:a:0 language="Untranslated"
{% if 'Translated' in audio_tracks %}
	-map 0:a:1 -b:a:1 96k -metadata:s:a:1 language="Translated"
{% endif %}
{% if 'Translated-2' in audio_tracks %}
	-map 0:a:2 -b:a:2 96k -metadata:s:a:2 language="Translated-2"
{% endif %}

	-f dash
	-window_size 201 -extra_window_size 10
	-seg_duration 3
	-dash_segment_type webm
	-init_seg_name 'init_$RepresentationID$.webm'
	-media_seg_name 'segment_$RepresentationID$_$Number$.webm'
	-adaptation_sets '{{ adaptation_sets | join(" ") }}'
	{{ dash_write_path }}/{{ stream }}/manifest.mpd
""")
	fanout_utils.call(command)



if __name__ == "__main__":
	parser = fanout_utils.setup_argparse(name="dash")

	parser.add_argument('--dash_write_path', metavar='PATH', type=str,
		help='Path to write the DASH-Pieces and Manifest to')

	args = parser.parse_args()

	fanout_utils.mainloop(name="hls", transcoding_stream="vpx", calback=fanout_dash, args=args)
