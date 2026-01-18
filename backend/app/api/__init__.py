from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api')

from app.api import tenants  # noqa: F401, E402
from app.api import servers  # noqa: F401, E402
from app.api import groups  # noqa: F401, E402
from app.api import labels  # noqa: F401, E402
from app.api import settings  # noqa: F401, E402
from app.api import policies  # noqa: F401, E402
from app.api import jobs  # noqa: F401, E402
from app.api import alerts  # noqa: F401, E402
from app.api import activity  # noqa: F401, E402
from app.api import analytics  # noqa: F401, E402
