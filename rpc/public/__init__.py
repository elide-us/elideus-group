from .links.handler import handle_links_request
from .vars.handler import handle_vars_request
from .users.handler import handle_users_request
from .gallery.handler import handle_gallery_request
from .pages.handler import handle_pages_request


HANDLERS: dict[str, callable] = {
  "links": handle_links_request,
  "vars": handle_vars_request,
  "users": handle_users_request,
  "gallery": handle_gallery_request,
  "pages": handle_pages_request,
}
