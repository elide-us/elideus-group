from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.cms_workbench_module import CmsWorkbenchModule
from server.modules.contract_query_builder_module import ContractQueryBuilderModule

from .models import (
  ServiceObjectsDeleteComponentPropertyParams1,
  ServiceObjectsDeleteDatabaseColumnParams1,
  ServiceObjectsDeleteDatabaseTableParams1,
  ServiceObjectsDeleteModuleMethodParams1,
  ServiceObjectsDeleteTypeParams1,
  ServiceObjectsDeleteTreeNodeParams1,
  ServiceObjectsDeleteTreeNodePropertyParams1,
  ServiceObjectsDeriveQueryParams1,
  ServiceObjectsGetMethodContractParams1,
  ServiceObjectsGetComponentDetailParams1,
  ServiceObjectsGetComponentTreeParams1,
  ServiceObjectsGetResolvedPropertiesParams1,
  ServiceObjectsGetModuleMethodsParams1,
  ServiceObjectsGetPageTreeParams1,
  ServiceObjectsGetTypeControlsParams1,
  ServiceObjectsListComponentsParams1,
  ServiceObjectsMoveTreeNodeParams1,
  ServiceObjectsReadChildrenParams1,
  ServiceObjectsReadDetailParams1,
  ServiceObjectsAnalyzePageParams1,
  ServiceObjectsCreateTreeNodeParams1,
  ServiceObjectsUpsertDatabaseColumnParams1,
  ServiceObjectsUpsertDatabaseTableParams1,
  ServiceObjectsUpsertComponentParams1,
  ServiceObjectsUpsertComponentPropertyParams1,
  ServiceObjectsUpdateTreeNodeParams1,
  ServiceObjectsUpsertModuleMethodParams1,
  ServiceObjectsUpsertTreeNodePropertyParams1,
  ServiceObjectsUpsertModuleParams1,
  ServiceObjectsUpsertTypeParams1,
)


async def service_objects_read_object_tree_children_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsReadChildrenParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.read_object_tree_children(params.categoryGuid, params.tableGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_read_object_tree_detail_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsReadDetailParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.read_object_tree_detail(params.tableGuid, params.maxRows)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_upsert_database_table_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsUpsertDatabaseTableParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.upsert_database_table(params.keyGuid, params.name, params.schema)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_delete_database_table_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsDeleteDatabaseTableParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.delete_database_table(params.keyGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_upsert_database_column_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsUpsertDatabaseColumnParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.upsert_database_column(
    params.keyGuid,
    params.tableGuid,
    params.typeGuid,
    params.name,
    params.ordinal,
    params.isNullable,
    params.isPrimaryKey,
    params.isIdentity,
    params.defaultValue,
    params.maxLength,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_delete_database_column_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsDeleteDatabaseColumnParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.delete_database_column(params.keyGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_upsert_type_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsUpsertTypeParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.upsert_type(
    params.keyGuid,
    params.name,
    params.mssqlType,
    params.postgresqlType,
    params.mysqlType,
    params.pythonType,
    params.typescriptType,
    params.jsonType,
    params.odbcTypeCode,
    params.maxLength,
    params.notes,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_delete_type_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsDeleteTypeParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.delete_type(params.keyGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_get_type_controls_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsGetTypeControlsParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.get_type_controls(params.typeGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_get_module_methods_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsGetModuleMethodsParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.get_module_methods(params.moduleGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_upsert_module_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsUpsertModuleParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.upsert_module(params.keyGuid, params.description, params.isActive)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_upsert_module_method_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsUpsertModuleMethodParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.upsert_module_method(
    params.keyGuid,
    params.moduleGuid,
    params.name,
    params.description,
    params.isActive,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_delete_module_method_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsDeleteModuleMethodParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.delete_module_method(params.keyGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_get_method_contract_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsGetMethodContractParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.get_method_contract(params.methodGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_get_page_tree_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsGetPageTreeParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.get_page_tree(params.pageGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_get_component_tree_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsGetComponentTreeParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.get_component_tree(params.componentGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_list_components_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsListComponentsParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.list_components()

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_get_component_detail_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsGetComponentDetailParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.get_component_detail(params.componentGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_upsert_component_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsUpsertComponentParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.upsert_component(
    params.keyGuid,
    params.description,
    params.defaultTypeGuid,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_create_tree_node_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsCreateTreeNodeParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.create_tree_node(
    params.pageGuid,
    params.parentGuid,
    params.componentGuid,
    params.label,
    params.fieldBinding,
    params.sequence,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_update_tree_node_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsUpdateTreeNodeParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.update_tree_node(
    params.keyGuid,
    params.label,
    params.fieldBinding,
    params.sequence,
    params.rpcOperation,
    params.rpcContract,
    params.componentGuid,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_delete_tree_node_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsDeleteTreeNodeParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.delete_tree_node(params.keyGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_move_tree_node_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsMoveTreeNodeParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.move_tree_node(
    params.keyGuid,
    params.newParentGuid,
    params.newSequence,
  )

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_analyze_page_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsAnalyzePageParams1.model_validate(rpc_request.payload or {})
  module: ContractQueryBuilderModule = request.app.state.contract_query_builder
  await module.on_ready()
  del auth_ctx

  result = await module.analyze_page(params.pageGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_derive_query_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsDeriveQueryParams1.model_validate(rpc_request.payload or {})
  module: ContractQueryBuilderModule = request.app.state.contract_query_builder
  await module.on_ready()
  del auth_ctx

  result = await module.derive_query(params.pageGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload={"query": result},
    version=rpc_request.version,
  )


async def service_objects_get_property_catalog_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.get_property_catalog()

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_get_resolved_properties_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsGetResolvedPropertiesParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.get_resolved_properties(params.componentGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_upsert_component_property_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsUpsertComponentPropertyParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.upsert_component_property(params.componentGuid, params.propertyGuid, params.value)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_upsert_tree_node_property_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsUpsertTreeNodePropertyParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.upsert_tree_node_property(params.treeNodeGuid, params.propertyGuid, params.value)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_delete_component_property_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsDeleteComponentPropertyParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.delete_component_property(params.componentGuid, params.propertyGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_delete_tree_node_property_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsDeleteTreeNodePropertyParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.delete_tree_node_property(params.treeNodeGuid, params.propertyGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )
