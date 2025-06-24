import unittest

from mwr_test.cinnibar.api import builders, frame_test
from mwr_test.cinnibar.reflection import reflected_array_test, reflected_null_test, reflected_object_test, reflected_primitive_test, reflected_string_test, reflected_type_test, reflector_test
from mwr_test.droidhg import android_test, console, modules, repoman, ssl

all_tests = unittest.TestSuite((
  builders.reflection_request_test.ReflectionRequestFactoryTestSuite(),
  builders.reflection_response_test.ReflectionResponseFactoryTestSuite(),
  builders.system_request_test.SystemRequestFactoryTestSuite(),
  builders.system_response_test.SystemResponseFactoryTestSuite(),

  #api.formatters.system_response_test

  frame_test.FrameTestSuite(),
  #api.reflection_message_test
  #api.system_message_test

  console.coloured_stream_test.ColouredStreamTestSuite(),
  #console.console_test
  #console.sequencer_test
  #console.server_test

  modules.import_conflict_resolver_test.ImportConflictResolverTestSuite(),
  modules.module_base_test.ModuleTestSuite(),
  #modules.common.assets
  #modules.common.toy_box
  #modules.common.file_system
  #modules.common.filtering
  #modules.common.formatter
  #modules.common.loader
  #modules.common.package_manager
  #modules.common.path_completion
  #modules.common.provider
  #modules.common.shell
  #modules.common.strings
  #modules.common.vulnerability
  #modules.common.zip_file

  reflected_array_test.ReflectedArrayTestSuite(),
  reflected_null_test.ReflectedNullTestSuite(),
  reflected_object_test.ReflectedObjectTestSuite(),
  reflected_string_test.ReflectedStringTestSuite(),
  reflected_primitive_test.ReflectedPrimitiveTestSuite(),
  reflected_type_test.ReflectedTypeTestSuite(),
  reflector_test.ReflectorTestSuite(),
  
  repoman.installer_test.ModuleInstallerTestSuite(),
  repoman.remote_test.RemoteTestSuite(),
  repoman.repository_builder_test.RepositoryBuilderTestSuite(),
  repoman.repository_test.RepositoryTestSuite(),
  
  ssl.ca.CATestSuite(),

  android_test.IntentTestSuite() ))
  #device_test
  #session_test

unittest.TextTestRunner().run(all_tests)
