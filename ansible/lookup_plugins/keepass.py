#!/usr/bin/env python3
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import getpass

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

try:
	from pykeepass import PyKeePass
except ImportError:
	raise AnsibleError(
		"pykeepass is missing - install with pip"\
		"(preferably into an virtualenv)"
	)

SAVED_PASSWORD = None

class LookupModule(LookupBase):
	FILENAME_ENV='KEEPASS'
	PASSWORD_ENV='KEEPASS_PW'

	password = None

	def run(self, terms, variables, **kwargs):
		filename = self.get_filename()
		password = self.get_password()

		ret = []
		kp = PyKeePass(filename, password)
		for term in terms:
			path, attribute = term.rsplit('.', 1)
			# pykeepass > 4.0 uses list for path
			if int(kp.version[0]) >= 4:
				path = path.split("/")
			found = kp.find_entries_by_path(path, first=True)

			if not found:
				raise AnsibleError(
						"Entry %s not found in keepass-Database %s" % \
						(path, filename)
					)

			if attribute.startswith('attr_'):
				dict = found.custom_properties
				value = dict[attribute[len('attr_'):]]
			else:
				value = getattr(found, attribute)

			ret.append(value)

		return ret

	def get_filename(self):
		filename = os.environ.get(LookupModule.FILENAME_ENV)

		if not filename:
			raise AnsibleError(
					"Environment-Variable %s not set" % \
					(LookupModule.FILENAME_ENV)
				)

		return filename

	def get_password(self):
		password = os.environ.get(LookupModule.PASSWORD_ENV)

		if not password:
			raise AnsibleError(
					"Environment-Variable %s not set" % \
					(LookupModule.PASSWORD_ENV)
				)

		return password

	def open_stdin(self):
		was_closed = sys.stdin.closed
		if was_closed:
			sys.stdin = open('/dev/tty')

		return was_closed

	def close_stdin(self):
		sys.stdin.close()

	def test_password(self):
		filename = self.get_filename()
		password = self.get_password()

		try:
			kp = PyKeePass(filename, password)
		except IOError:
			return False

		return True

if __name__ == '__main__':
	module = LookupModule()
	if len(sys.argv) < 2:
		if not module.test_password():
			print('Password not valid for Keepass-File')
			sys.exit(42)
	else:
		print(module.run([sys.argv[1]], None)[0])

