"""OpenText Content Server Connector entrypoint."""
from __future__ import annotations

import handlers_audit  # noqa: F401
import handlers_categories  # noqa: F401
import handlers_connection  # noqa: F401
import handlers_documents  # noqa: F401
import handlers_nodes  # noqa: F401
import handlers_permissions  # noqa: F401
import handlers_versions  # noqa: F401
import panels  # noqa: F401
import panels_center  # noqa: F401
import panels_settings  # noqa: F401
from app import ext

extension = ext
