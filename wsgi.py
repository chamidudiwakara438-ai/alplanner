# PythonAnywhere (or any WSGI host) entry point for AL Planner.
#
# On PythonAnywhere: Web tab → "WSGI configuration file" → delete the
# template there and paste THIS file's contents (or set the path to it).
# No changes needed — paths auto-detect from this file's location.
import os, sys

project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)
os.chdir(project_home)

# Database + uploads + static files live INSIDE the project folder,
# so they persist exactly like on your own PC.
os.environ.setdefault('AL_DATA_DIR', os.path.join(project_home, 'data'))
os.environ.setdefault('AL_UPLOAD_DIR', os.path.join(project_home, 'uploads'))
os.environ.setdefault('AL_PUBLIC_DIR', os.path.join(project_home, 'public'))

from server import app as application   # WSGI servers call `application`
