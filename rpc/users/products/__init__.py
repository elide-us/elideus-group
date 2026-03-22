from .services import users_products_list_v1, users_products_purchase_v1


DISPATCHERS = {
  ("list", "1"): users_products_list_v1,
  ("purchase", "1"): users_products_purchase_v1,
}
