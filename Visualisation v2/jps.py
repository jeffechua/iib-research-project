from sparql import *
from config import *
from py4jps.resources import JpsBaseLib

__all__ = ['remote_client']

# Instantiate and start resource gateway object to JPS_BASE_LIB
jpsBaseLibGW = JpsBaseLib()
jpsBaseLibGW.launchGateway()

# Create a JVM module view and use it to import the required java classes
jpsBaseLibView = jpsBaseLibGW.createModuleView()
jpsBaseLibGW.importPackages(jpsBaseLibView, "uk.ac.cam.cares.jps.base.query.*")
# jpsBaseLibGW.importPackages(jpsBaseLibView, "uk.ac.cam.cares.jps.base.timeseries.*")

remote_client = jpsBaseLibView.RemoteStoreClient(QUERY_ENDPOINT, UPDATE_ENDPOINT)