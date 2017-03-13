#!/usr/bin/python
import sys

import roslib

import gencpp
import genmsg

from  roslib import packages,msgs
import os

from cStringIO import StringIO

import argparse

import parse_subsystem_xml

NAME='create_boost_header'

MSG_TYPE_TO_CPP = {'byte': 'int8_t',
                   'char': 'uint8_t',
                   'bool': 'uint8_t',
                   'uint8': 'uint8_t',
                   'int8': 'int8_t',
                   'uint16': 'uint16_t',
                   'int16': 'int16_t',
                   'uint32': 'uint32_t',
                   'int32': 'int32_t',
                   'uint64': 'uint64_t',
                    'int64': 'int64_t',
                   'float32': 'float',
                   'float64': 'double',
                   'string': 'std::basic_string<char, std::char_traits<char>, typename ContainerAllocator::template rebind<char>::other > ',
                   'time': 'ros::Time',
                   'duration': 'ros::Duration'}

#used
def msg_type_to_cpp(type):
    """
    Converts a message type (e.g. uint32, std_msgs/String, etc.) into the C++ declaration
    for that type (e.g. uint32_t, std_msgs::String_<ContainerAllocator>)

    @param type: The message type
    @type type: str
    @return: The C++ declaration
    @rtype: str
    """
    (base_type, is_array, array_len) = genmsg.msgs.parse_type(type)
    cpp_type = None
    if (genmsg.msgs.is_builtin(base_type)):
        cpp_type = MSG_TYPE_TO_CPP[base_type]
    elif (len(base_type.split('/')) == 1):
        if (genmsg.msgs.is_header_type(base_type)):
            cpp_type = ' ::std_msgs::Header '
        else:
            cpp_type = '%s '%(base_type)
    else:
        pkg = base_type.split('/')[0]
        msg = base_type.split('/')[1]
        cpp_type = ' ::%s::%s '%(pkg, msg)

    if (is_array):
        if (array_len is None):
            raise
        else:
            return 'boost::array<%s, %s> '%(cpp_type, array_len)
    else:
        return cpp_type

def write_boost_includes(s, spec, port_spec_dict):
    """
    Writes the message-specific includes

    @param s: The stream to write to
    @type s: stream
    @param spec: The message spec to iterate over
    @type spec: roslib.msgs.MsgSpec
    @param serializer: The serializer type for which to include headers
    @type serializer: str
    """
    for field in spec.parsed_fields():
        if (not field.is_builtin):
            if field.name in port_spec_dict:
                port_spec = port_spec_dict[field.name]
                if port_spec[0] == 'container':
                    (pkg, name) = genmsg.names.package_resource_name(field.base_type)
                    pkg = (pkg or spec.package) # convert '' to this package
                    s.write('#include <%s/subsystem_ports/%s.h>\n'%(pkg,  name))

    s.write('\n')

def parse_comment_to_subsystem_buffer_spec(comment):
    id_str = 'subsystem_buffer{'

    pos_beg = comment.find(id_str)
    if pos_beg < 0:
        return None

    pos_end = comment.find('}', pos_beg)
    if pos_end < 0:
        # subsystem_buffer declaration must be complete
        return None

    decl = comment[pos_beg + len(id_str) : pos_end]
    decl_list = decl.split(';')

    decl_dict = {}
    for item in decl_list:
        pos = item.find(':')
        if pos < 0:
            continue
        decl_dict[item[:pos].strip()] = item[pos+1:].strip()

    if not 'type' in decl_dict:
        return None
    type = decl_dict['type']

    validity_field_name = ''
    if 'validity' in decl_dict:
        validity_field_name = decl_dict['validity']

    return (type, validity_field_name)

def get_port_spec_dict(spec):
    port_spec_dict = {}
    # process msg declaration line by line, search for port_spec
    for line in spec.text.splitlines():
        comment_start = line.find('#')
        if comment_start <= 0:
            continue
        declaration = line[:comment_start-1]
        comment = line[comment_start:]
        success = True
        try:
            field_type, name = genmsg.msg_loader._load_field_line(declaration, spec.package)
        except:
            success = False
        if success:
            port_spec = parse_comment_to_subsystem_buffer_spec(comment)
            if port_spec != None:
                port_spec_dict[name] = port_spec

    return port_spec_dict

def write_boost_serialization(s, spec, cpp_name_prefix):
    """
    Writes the boost::serialize function for a message

    @param s: Stream to write to
    @type s: stream
    @param spec: The message spec
    @type spec: roslib.msgs.MsgSpec
    @param cpp_name_prefix: The C++ prefix to prepend to a message to refer to it (e.g. "std_msgs::")
    @type cpp_name_prefix: str
    """
    (cpp_msg_unqualified, cpp_msg_with_alloc, _) = gencpp.cpp_message_declarations(cpp_name_prefix, spec.short_name)

    port_spec_dict = get_port_spec_dict(spec)

    s.write("/* Auto-generated by TODO for TODO */\n")

    s.write('#include <%s/subsystem_ports/%s.h>\n'%(spec.package, spec.short_name))
#    write_boost_includes(s, spec, port_spec_dict)
    s.write('#include <common_interfaces/message_concate.h>\n')
    s.write('#include <common_interfaces/message_split.h>\n')
    s.write('#include <common_interfaces/interface_tx.h>\n')
    s.write('#include <common_interfaces/interface_rx.h>\n')
    s.write('#include <rtt/Component.hpp>\n\n')

    s.write('namespace %s {\n\n'%(spec.package))
    s.write('typedef MessageConcate<%s_InputPorts > %sConcate;\n'%(spec.short_name, spec.short_name))
    s.write('typedef MessageSplit<%s_OutputPorts > %sSplit;\n'%(spec.short_name, spec.short_name))
    s.write('typedef InterfaceTx<%s > %sTx;\n'%(spec.short_name, spec.short_name))
    s.write('typedef InterfaceRx<%s > %sRx;\n'%(spec.short_name, spec.short_name))
    s.write('} // namespace %s\n\n'%(spec.package))

    s.write('typedef %s::%sConcate %s_%sConcate;\n'%(spec.package, spec.short_name, spec.package, spec.short_name))
    s.write('ORO_LIST_COMPONENT_TYPE(%s_%sConcate)\n'%(spec.package, spec.short_name))

    s.write('typedef %s::%sSplit %s_%sSplit;\n'%(spec.package, spec.short_name, spec.package, spec.short_name))
    s.write('ORO_LIST_COMPONENT_TYPE(%s_%sSplit)\n'%(spec.package, spec.short_name))

    s.write('typedef %s::%sTx %s_%sTx;\n'%(spec.package, spec.short_name, spec.package, spec.short_name))
    s.write('ORO_LIST_COMPONENT_TYPE(%s_%sTx)\n'%(spec.package, spec.short_name))

    s.write('typedef %s::%sRx %s_%sRx;\n'%(spec.package, spec.short_name, spec.package, spec.short_name))
    s.write('ORO_LIST_COMPONENT_TYPE(%s_%sRx)\n'%(spec.package, spec.short_name))

def generate_boost_serialization(package, port_def, output_cpp):
    """
    Generate a boost::serialization header

    @param msg_path: The path to the .msg file
    @type msg_path: str
    """
    mc = genmsg.msg_loader.MsgContext()

#    spec = genmsg.msg_loader.load_msg_from_file(mc, msg_path, msg_type)
#    cpp_prefix = '%s::'%(package)

    with open(port_def, 'r') as f:
        read_data = f.read()

    sd = parse_subsystem_xml.parseSubsystemXml(read_data)

    s = StringIO()
    s.write("// autogenerated by rtt_subsystem_ports/create_master_h.py\n")
    s.write("// do not modify this file\n\n")

    header_name = package.upper() + "_MASTER_H__"
    s.write("#ifndef " + header_name + "\n")
    s.write("#define " + header_name + "\n\n")

    s.write("#include \"common_behavior/input_data.h\"\n")
    s.write("#include \"common_behavior/abstract_behavior.h\"\n")
    s.write("#include \"common_behavior/abstract_state.h\"\n\n")


    for p_in in sd.ports_in:
        s.write("#include \"" + p_in.type_pkg + "/" + p_in.type_name + ".h\"\n")

    s.write("\nnamespace " + package + "_types {\n\n")

    #
    # class InputData
    #
    s.write("class InputData : public common_behavior::InputData {\n")
    s.write("public:\n")

    for p_in in sd.ports_in:
        s.write("  " + p_in.type_pkg + "::" + p_in.type_name + " " + p_in.short_name + ";\n")

    s.write("};\n\n")

    #
    # errors
    #
    s.write("enum {\n")
    for e in sd.errors:
        s.write("  " + e + "_bit,\n")
    s.write("  ERROR_ENUM_SIZE\n};\n\n")

    s.write("typedef common_behavior::ConditionCause<ERROR_ENUM_SIZE > ErrorCause;\n")
    s.write("typedef boost::shared_ptr<ErrorCause > ErrorCausePtr;\n")
    s.write("typedef boost::shared_ptr<const ErrorCause > ErrorCauseConstPtr;\n\n")

    s.write("std::string getErrorReasonStr(ErrorCauseConstPtr err);\n\n")

    #
    # behavior base class
    #
    s.write("class BehaviorBase : public common_behavior::BehaviorBase {\n")
    s.write("public:\n")
    s.write("  bool checkErrorCondition(\n")
    s.write("      const boost::shared_ptr<common_behavior::InputData >& in_data,\n")
    s.write("      const std::vector<RTT::TaskContext*> &components,\n")
    s.write("      common_behavior::AbstractConditionCausePtr result = common_behavior::AbstractConditionCausePtr()) const {\n")
    s.write("    return checkErrorCondition( boost::static_pointer_cast<InputData >(in_data),\n")
    s.write("                                components,\n")
    s.write("                                boost::dynamic_pointer_cast<ErrorCause >(result) );\n")
    s.write("  }\n\n")

    s.write("  bool checkStopCondition(\n")
    s.write("      const boost::shared_ptr<common_behavior::InputData >& in_data,\n")
    s.write("      const std::vector<RTT::TaskContext*> &components) const {\n")
    s.write("    return checkStopCondition( boost::static_pointer_cast<InputData >(in_data), components);\n")
    s.write("  }\n\n")

    s.write("  virtual bool checkErrorCondition(\n")
    s.write("      const boost::shared_ptr<InputData >& in_data,\n")
    s.write("      const std::vector<RTT::TaskContext*> &components,\n")
    s.write("      ErrorCausePtr result) const = 0;\n\n")

    s.write("  virtual bool checkStopCondition(\n")
    s.write("      const boost::shared_ptr<InputData >& in_data,\n")
    s.write("      const std::vector<RTT::TaskContext*> &components) const = 0;\n\n")

    s.write("protected:\n")
    s.write("  BehaviorBase(const std::string& name, const std::string& short_name)\n")
    s.write("      : common_behavior::BehaviorBase(name, short_name)\n")
    s.write("  { }\n")
    s.write("};\n\n")

    #
    # state base class
    #
    s.write("class StateBase : public common_behavior::StateBase {\n")
    s.write("public:\n")
    s.write("    bool checkInitialCondition(\n")
    s.write("            const boost::shared_ptr<common_behavior::InputData >& in_data,\n")
    s.write("            const std::vector<RTT::TaskContext*> &components,\n")
    s.write("            const std::string& prev_state_name,\n")
    s.write("            bool in_error) const {\n")
    s.write("        return checkInitialCondition(boost::static_pointer_cast<InputData >(in_data), components, prev_state_name, in_error);\n")
    s.write("    }\n\n")

    s.write("    virtual bool checkInitialCondition(\n")
    s.write("            const boost::shared_ptr<InputData >& in_data,\n")
    s.write("            const std::vector<RTT::TaskContext*> &components,\n")
    s.write("            const std::string& prev_state_name,\n")
    s.write("            bool in_error) const = 0;\n\n")

    s.write("protected:\n")
    s.write("    StateBase(const std::string& state_name, const std::string& short_state_name, const std::string& behavior_name) :\n")
    s.write("        common_behavior::StateBase(state_name, short_state_name, behavior_name)\n")
    s.write("    { }\n")
    s.write("};\n")

    s.write("};  // namespace " + package + "_types\n\n")

    s.write("#endif  // " + header_name + "\n")


#    write_boost_serialization(s, spec, cpp_prefix)

    (output_dir,filename) = os.path.split(output_cpp)
    try:
        os.makedirs(output_dir)
    except OSError, e:
        pass

    f = open(output_cpp, 'w')
    print >> f, s.getvalue()

    s.close()


def create_boost_headers(argv, stdout, stderr):
    parser = argparse.ArgumentParser(description='Generate boost serialization header for ROS message.')
    parser.add_argument('pkg',metavar='PKG',type=str, nargs=1,help='The package name.')
    parser.add_argument('port_def',metavar='PORT_DEF',type=str, nargs=1,help='Port definition file.')
    parser.add_argument('output_cpp',metavar='OUTPUT_CPP',type=str, nargs=1,help='Output cpp file.')

    args = parser.parse_args()

    print args.pkg[0], args.port_def[0], args.output_cpp[0]

    generate_boost_serialization(args.pkg[0], args.port_def[0], args.output_cpp[0])

if __name__ == "__main__":
    try:
        create_boost_headers(sys.argv, sys.stdout, sys.stderr)
    except Exception, e:
        sys.stderr.write("Failed to generate boost headers: " + str(e))
        raise
        #sys.exit(1)
