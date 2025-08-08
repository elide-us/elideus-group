# Registry is managed from here, each RPC namespace function that requires a database 
# lookup should have an entry here which maps to the _provider/registry.py that contains 
# the appropriate query for that database provider. The idea being that the database 
# module provides a standard response interface for services, but internally depending 
# on the database provider selected, the correcly formatted TSQL is executed on the 
# selected database and the response is then given back through the database module layer.

# I think this workflow illustrates this, please organize this all in a clean manner:
# 
#  SERVICE->Query => DATABASE->Registry(QUERY) => PROVIDER(QUERY)->SQLServer<T>(QUERY) => (RESPONSE)