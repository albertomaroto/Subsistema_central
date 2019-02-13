#!/usr/bin/env python
import os
import sys
import subprocess
from gestion import nodos

if __name__ == '__main__':
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subsistema_central.settings')
	if (os.environ.get('RUN_MAIN') != 'true' and len(sys.argv) > 1 and sys.argv[1] == "runserver"):
		nodos.iniciar_servidor_nodos()
		#subprocess.Popen(['python','nodos.py'])
	try:
		from django.core.management import execute_from_command_line
	except ImportError as exc:
		raise ImportError(
			"Couldn't import Django. Are you sure it's installed and "
			"available on your PYTHONPATH environment variable? Did you "
			"forget to activate a virtual environment?"
		) from exc
	execute_from_command_line(sys.argv)
