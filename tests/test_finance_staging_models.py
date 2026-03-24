from rpc.finance.staging.models import StagingLineItem1


def test_staging_line_item_coerces_numeric_decimal_fields_to_strings():
  line_item = StagingLineItem1(
    recid=1,
    imports_recid=2,
    vendors_recid=3,
    element_quantity=0.0,
    element_unit_price=None,
    element_amount=12.5,
  )

  assert line_item.element_quantity == "0.0"
  assert line_item.element_unit_price == "0"
  assert line_item.element_amount == "12.5"
