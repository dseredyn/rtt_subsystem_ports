find_package(OROCOS-RTT 2.0.0 COMPONENTS rtt-scripting rtt-marshalling)
if (NOT OROCOS-RTT_FOUND)
  message(FATAL_ERROR "\n   RTT not found. Is the version correct? Use the CMAKE_PREFIX_PATH cmake or environment variable to point to the installation directory of RTT.")
else()
  include(${OROCOS-RTT_USE_FILE_PATH}/UseOROCOS-RTT.cmake)
  #add_definitions( -DRTT_COMPONENT )
endif()

include(AddFileDependencies)

#find_package(catkin REQUIRED message_generation)

# Configure source and destination paths of generated files
msgs_from_ec_config_destinations()

# Check if we're generating code for messages in this package
if("${_package}" STREQUAL "${PROJECT_NAME}")
  set(${_package}_FOUND True)
else()
  find_package(${_package} QUIET)
endif()

#find_package(genmsg REQUIRED)

# Set the subsystem ports header generation script path
set(CREATE_MSGS_FROM_EC_CONFIG_EXE_PATH ${rtt_subsystem_ports_DIR}/create_msgs_from_ec_config.py)

# Set the subsystem ports sources generation script path
#set(CREATE_SUBSYSTEM_PORTS_SOURCE_EXE_PATH ${rtt_subsystem_ports_DIR}/create_subsystem_ports_source.py)

# Set the subsystem ports components' sources generation script path
#set(CREATE_COMPONENTS_SOURCE_EXE_PATH ${rtt_subsystem_ports_DIR}/create_components_source.py)

# Store the ros package name
set(ROSPACKAGE ${_package})
set(ECCONFIGFILE ${_config_file})

set(ECCONFIG_DIR "${PROJECT_SOURCE_DIR}/ec_config")

safe_execute_process(COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${CREATE_MSGS_FROM_EC_CONFIG_EXE_PATH} ${_package} ${ECCONFIG_DIR}/${ECCONFIGFILE} ${CATKIN_DEVEL_PREFIX}/share/${PROJECT_NAME}/msg)
#safe_execute_process(COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${CREATE_MSGS_FROM_EC_CONFIG_EXE_PATH} ${_package} ${ECCONFIG_DIR}/${ECCONFIGFILE} ${CMAKE_CURRENT_BINARY_DIR}/msg)

#get_filename_component(ACTION_SHORT_NAME ${actionfile} NAME_WE)
set(MESSAGE_DIR ${CATKIN_DEVEL_PREFIX}/share/${PROJECT_NAME}/msg)
#set(MESSAGE_DIR ${CMAKE_CURRENT_BINARY_DIR}/msg)

file(GLOB ARG_FILES RELATIVE "${MESSAGE_DIR}" "${MESSAGE_DIR}/*.msg")
list(SORT ARG_FILES)

set(OUTPUT_FILES ${ARG_FILES})
#  Test.msg
#)

#_prepend_path(${MESSAGE_DIR}/ "${OUTPUT_FILES}" OUTPUT_FILES_W_PATH)

#message(STATUS "Generating .msg files for action ${PROJECT_NAME}/${ACTION_SHORT_NAME} ${actionfile}")

#stamp(${actionfile})

#if(NOT CATKIN_ENV)
#  message(FATAL_ERROR "Assertion failed: 'CATKIN_ENV' is not set")
#endif()
#if(${actionfile} IS_NEWER_THAN ${MESSAGE_DIR}/${ACTION_SHORT_NAME}Action.msg)
#  safe_execute_process(COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENACTION_BIN} ${actionfile} -o ${MESSAGE_DIR})
#endif()

add_message_files(
  BASE_DIR ${MESSAGE_DIR}
  FILES ${OUTPUT_FILES})

generate_messages()
#catkin_package()
#  CATKIN_DEPENDS message_runtime)

