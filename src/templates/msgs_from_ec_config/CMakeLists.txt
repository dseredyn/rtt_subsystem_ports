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

#add_message_files(
#  BASE_DIR ${MESSAGE_DIR}
#  FILES ${OUTPUT_FILES})

#generate_messages()

#  cmake_parse_arguments(ARG "" "" "DEPENDENCIES;LANGS" ${ARGN})

#  if(${PROJECT_NAME}_GENERATE_MESSAGES)
#    message(FATAL_ERROR "generate_messages() must only be called once per project'")
#  endif()

#  if(ARG_UNPARSED_ARGUMENTS)
#    message(FATAL_ERROR "generate_messages() called with unused arguments: ${ARG_UNPARSED_ARGUMENTS}")
#  endif()

#  if(${PROJECT_NAME}_CATKIN_PACKAGE)
#    message(FATAL_ERROR "generate_messages() must be called before catkin_package() in project '${PROJECT_NAME}'")
#  endif()

#  set(ARG_MESSAGES ${${PROJECT_NAME}_MESSAGE_FILES})
#  set(ARG_SERVICES ${${PROJECT_NAME}_SERVICE_FILES})
#  set(ARG_DEPENDENCIES ${ARG_DEPENDENCIES})

#set(GEN_LANGS "${GEN_LANGS}" PARENT_SCOPE)
#set(genmsg_CMAKE_DIR "${genmsg_CMAKE_DIR}" PARENT_SCOPE)
#set(PKG_MSG_INCLUDE_DIRS "${PKG_MSG_INCLUDE_DIRS}" PARENT_SCOPE)
#set(PKG_MSG_FILES "${PKG_MSG_FILES}" PARENT_SCOPE)
#set(PKG_SRV_FILES "${PKG_SRV_FILES}" PARENT_SCOPE)
#set(MSG_INCLUDE_DIRS "${MSG_INCLUDE_DIRS}" PARENT_SCOPE)
#set(${PROJECT_NAME}_GENERATE_MESSAGES "${${PROJECT_NAME}_GENERATE_MESSAGES}" PARENT_SCOPE)

#set(package_has_static_sources "${package_has_static_sources}" PARENT_SCOPE)

#set(workspaces "${workspaces}" PARENT_SCOPE)


#set(ARG_MESSAGES "${ARG_MESSAGES}" PARENT_SCOPE)
#set(ARG_SERVICES "${ARG_SERVICES}" PARENT_SCOPE)
#set(ARG_DEPENDENCIES "${ARG_DEPENDENCIES}" PARENT_SCOPE)

#set(all_deps "${all_deps}" PARENT_SCOPE)
#set(handled_deps "${handled_deps}" PARENT_SCOPE)
#set(pending_deps "${pending_deps}" PARENT_SCOPE)

#set(MSG_I_FLAGS "${MSG_I_FLAGS}" PARENT_SCOPE)


#message(ERROR "${PROJECT_NAME}_GENERATE_MESSAGES: ${${PROJECT_NAME}_GENERATE_MESSAGES}")
#message(ERROR "PKG_MSG_FILES: ${PKG_MSG_FILES}")

#set(ARG_DIRECTORY "${ARG_DIRECTORY}" PARENT_SCOPE)

#set(${PROJECT_NAME}_CFG_EXTRAS "${${PROJECT_NAME}_CFG_EXTRAS}" PARENT_SCOPE)


#catkin_package()
#  CATKIN_DEPENDS message_runtime)

#set(${_package}_MESSAGE_FILES ${${_package}_MESSAGE_FILES} PARENT_SCOPE)

set(MESSAGE_DIR "${MESSAGE_DIR}" PARENT_SCOPE)
set(OUTPUT_FILES "${OUTPUT_FILES}" PARENT_SCOPE)


