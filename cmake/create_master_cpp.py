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
    s.write("#include <rtt/plugin/ServicePlugin.hpp>\n")
    s.write("#include <rtt/extras/PeriodicActivity.hpp>\n")
    s.write("#include \"rtt/Logger.hpp\"\n")
    s.write("#include <rtt/base/DataObjectLockFree.hpp>\n")
    s.write("#include <ros/param.h>\n")
    s.write("#include <rtt_rosclock/rtt_rosclock.h>\n")


    s.write("#include \"common_behavior/master_service.h\"\n")
    s.write("#include \"" + package + "/master.h\"\n")

    s.write("\nnamespace " + package + "_types {\n\n")

    s.write("class " + package + "_Master : public common_behavior::MasterService {\n")
    s.write("public:\n")
    s.write("    explicit " + package + "_Master(RTT::TaskContext* owner)\n")
    s.write("        : common_behavior::MasterService(owner)\n")
    s.write("        , owner_(owner)\n")
    for p_in in sd.ports_in:
        s.write("        , " + p_in.short_name + "_no_data_counter_(1000)\n")
        s.write("        , port_" + p_in.short_name + "_in_(\"" + p_in.name + "_INPORT\")\n")
        s.write("        , port_" + p_in.short_name + "_out_(\"" + p_in.name + "_OUTPORT\")\n")
    s.write("        , port_no_data_trigger_in__(\"no_data_trigger_INPORT_\")\n")
    s.write("    {\n")

    for p_in in sd.ports_in:
        if p_in.event:
            s.write("        owner_->addEventPort(port_" + p_in.short_name + "_in_);\n")
        else:
            s.write("        owner_->addPort(port_" + p_in.short_name + "_in_);\n")
        s.write("        owner_->addPort(port_" + p_in.short_name + "_out_);\n\n")

    s.write("\n        owner_->addEventPort(port_no_data_trigger_in__);\n")

    s.write("        bool use_sim_time = false;\n")
    s.write("        ros::param::get(\"/use_sim_time\", use_sim_time);\n")
    s.write("        if (use_sim_time) {\n")
#        s.write("        bool use_sim_time = false;\n")
#        s.write("        ros::param::get(\"/use_sim_time\", use_sim_time);\n")
#        s.write("        if (use_sim_time) {\n")
    if sd.trigger_gazebo:
        s.write("            if (!boost::dynamic_pointer_cast<RTT::internal::GlobalService >(RTT::internal::GlobalService::Instance())->require(\"gazebo_rtt_service\")) {\n")
        s.write("                RTT::Logger::log() << RTT::Logger::Error << \"could not load service 'gazebo_rtt_service'\" << RTT::Logger::endl;\n")
        s.write("            }\n")
        s.write("            else {\n")
        s.write("                RTT::Service::shared_ptr gazebo_rtt_service = RTT::internal::GlobalService::Instance()->getService(\"gazebo_rtt_service\");\n")
        s.write("                RTT::OperationInterfacePart *singleStepOp = gazebo_rtt_service->getOperation(\"singleStep\");\n")
        s.write("                if (singleStepOp == NULL) {\n")
        s.write("                    RTT::Logger::log() << RTT::Logger::Error << \"the service \" << gazebo_rtt_service->getName() << \" has no matching operation singleStep\" << RTT::Logger::endl;\n")
        s.write("                }\n")
        s.write("                else {\n")
        s.write("                    singleStep_ =  RTT::OperationCaller<void()>(singleStepOp);\n")
        s.write("                }\n")
        s.write("            }\n")

    if sd.use_ros_sim_clock:
        s.write("             rtt_rosclock::use_ros_clock_topic();\n")

#        s.write("            RTT::Service::shared_ptr rosclock = RTT::internal::GlobalService::Instance()->getService(\"ros\")->getService(\"clock\");\n")
#
#        s.write("            RTT::Service::shared_ptr rosclock = RTT::internal::GlobalService::Instance()->getService(\"ros\")->getService(\"clock\");\n")
#        s.write("            if (!rosclock) {\n")
#        s.write("                RTT::Logger::log() << RTT::Logger::Error << \"could not get 'ros.clock' service\" << RTT::Logger::endl;\n")
#        s.write("            }\n")
#        s.write("            else {\n")
#        s.write("                RTT::OperationCaller<void()> useROSClockTopic = rosclock->getOperation(\"useROSClockTopic\");\n")
#        s.write("                if (!useROSClockTopic.ready()) {\n")
#        s.write("                    RTT::Logger::log() << RTT::Logger::Error << \"could not get 'useROSClockTopic' operation of 'ros.clock'\" << RTT::Logger::endl;\n")
#        s.write("                }\n")
#        s.write("                else {\n")
#        s.write("                    useROSClockTopic();\n")
#        s.write("                }\n")
#        s.write("            }\n")
    else:
        s.write("            rtt_rosclock::use_manual_clock();\n")

    s.write("            rtt_rosclock::enable_sim();\n")

    s.write("        }\n")

    if sd.period != None:
        if sd.use_sim_clock:
            s.write("            owner->loadService(\"sim_clock_activity\");\n")
        s.write("        owner->setPeriod(" + str(sd.period) + ");\n")

#    s.write("        }\n")

    s.write("    }\n\n")

    s.write("    virtual ~" + package + "_Master() {\n")
    s.write("    }\n\n")

    s.write("    virtual void initBuffers(boost::shared_ptr<common_behavior::InputData >& in_data) const {\n")
    s.write("        boost::shared_ptr<InputData > in = boost::static_pointer_cast<InputData >(in_data);\n")
    for p_in in sd.ports_in:
        s.write("        in->" + p_in.short_name + " = " + p_in.type_pkg + "::" + p_in.type_name + "();\n")
    s.write("    }\n\n")

    s.write("    virtual void readIpcPorts(boost::shared_ptr<common_behavior::InputData >& in_data) {\n")
    s.write("        boost::shared_ptr<InputData > in = boost::static_pointer_cast<InputData >(in_data);\n")
    for p_in in sd.ports_in:
        if not p_in.ipc:
            continue
        no_data_max = 50
        if p_in.event:
            no_data_max = 50
        s.write("        if (port_" + p_in.short_name + "_in_.read(in->" + p_in.short_name + ", false) != RTT::NewData) {\n")
        s.write("            if (" + p_in.short_name + "_no_data_counter_ >= " + str(no_data_max) + ") {\n")
        s.write("                in->" + p_in.short_name + " = " + p_in.type_pkg + "::" + p_in.type_name + "();\n")
        s.write("            }\n")
        s.write("            else {\n")
        s.write("                " + p_in.short_name + "_no_data_counter_++;\n")
        s.write("                in->" + p_in.short_name + " = " + p_in.short_name + "_prev_;\n")
        s.write("            }\n")
        s.write("        }\n")
        s.write("        else {\n")
        s.write("            " + p_in.short_name + "_no_data_counter_ = 0;\n")
        s.write("            " + p_in.short_name + "_prev_ = in->" + p_in.short_name + ";\n")
        s.write("        }\n")
    s.write("    }\n\n")

    s.write("    virtual void readInternalPorts(boost::shared_ptr<common_behavior::InputData >& in_data) {\n")
    s.write("        boost::shared_ptr<InputData > in = boost::static_pointer_cast<InputData >(in_data);\n")
    for p_in in sd.ports_in:
        if p_in.ipc:
            continue
        s.write("        if (port_" + p_in.short_name + "_in_.read(in->" + p_in.short_name + ", false) != RTT::NewData) {\n")
        s.write("            in->" + p_in.short_name + " = " + p_in.type_pkg + "::" + p_in.type_name + "();\n")
        s.write("        }\n")
    s.write("    }\n\n")

    s.write("    virtual void writePorts(boost::shared_ptr<common_behavior::InputData>& in_data) {\n")
    s.write("        boost::shared_ptr<InputData> in = boost::static_pointer_cast<InputData >(in_data);\n")
    for p_in in sd.ports_in:
        s.write("        port_" + p_in.short_name + "_out_.write(in->" + p_in.short_name + ");\n")
    s.write("    }\n\n")

    s.write("    virtual boost::shared_ptr<common_behavior::InputData > getDataSample() const {\n")
    s.write("        boost::shared_ptr<InputData > ptr(new InputData());\n")
    for p_in in sd.ports_in:
        s.write("        ptr->" + p_in.short_name + " = " + p_in.type_pkg + "::" + p_in.type_name + "();\n")
    s.write("        return boost::static_pointer_cast<common_behavior::InputData >( ptr );\n")
    s.write("    }\n\n")

    s.write("    virtual void getLowerInputBuffers(std::vector<common_behavior::InputBufferInfo >& info) const {\n")
    s.write("        info = std::vector<common_behavior::InputBufferInfo >();\n")
    for p in sd.ports_in:
        if p.side == 'bottom':
            if p.event:
                s.write("        info.push_back(common_behavior::InputBufferInfo(" + str(p.ipc).lower() + ", \"" + p.type_pkg + "_" + p.type_name + "\", \"" + p.name + "\", true, " + str(p.period_min) + ", " + str(p.period_avg) + ", " + str(p.period_max) + "));\n")
            else:
                s.write("        info.push_back(common_behavior::InputBufferInfo(" + str(p.ipc).lower() + ", \"" + p.type_pkg + "_" + p.type_name + "\", \"" + p.name + "\"));\n")
    s.write("    }\n\n")

    s.write("    virtual void getUpperInputBuffers(std::vector<common_behavior::InputBufferInfo >& info) const {\n")
    s.write("        info = std::vector<common_behavior::InputBufferInfo >();\n")
    for p in sd.ports_in:
        if p.side == 'top':
            if p.event:
                s.write("        info.push_back(common_behavior::InputBufferInfo(" + str(p.ipc).lower() + ", \"" + p.type_pkg + "_" + p.type_name + "\", \"" + p.name + "\", true, " + str(p.period_min) + ", " + str(p.period_avg) + ", " + str(p.period_max) + "));\n")
            else:
                s.write("        info.push_back(common_behavior::InputBufferInfo(" + str(p.ipc).lower() + ", \"" + p.type_pkg + "_" + p.type_name + "\", \"" + p.name + "\"));\n")
    s.write("    }\n\n")

    s.write("    virtual void getLowerOutputBuffers(std::vector<common_behavior::OutputBufferInfo >& info) const {\n")
    s.write("        info = std::vector<common_behavior::OutputBufferInfo >();\n")
    for p in sd.ports_out:
        if p.side == 'bottom':
            s.write("        info.push_back(common_behavior::OutputBufferInfo(" + str(p.ipc).lower() + ", \"" + p.type_pkg + "_" + p.type_name + "\", \"" + p.name + "\"));\n")
    s.write("    }\n\n")

    s.write("    virtual void getUpperOutputBuffers(std::vector<common_behavior::OutputBufferInfo >& info) const {\n")
    s.write("        info = std::vector<common_behavior::OutputBufferInfo >();\n")
    for p in sd.ports_out:
        if p.side == 'top':
            s.write("        info.push_back(common_behavior::OutputBufferInfo(" + str(p.ipc).lower() + ", \"" + p.type_pkg + "_" + p.type_name + "\", \"" + p.name + "\"));\n")
    s.write("    }\n\n")

    s.write("    virtual std::vector<std::string > getStates() const {\n")
    s.write("        return std::vector<std::string >({\n")
    for st in sd.states:
        s.write("                   \"" + st + "\",\n")
    s.write("                   \"" + sd.initial_state + "\"});\n")
    s.write("    }\n\n")

    s.write("    virtual std::string getInitialState() const {\n")
    s.write("        return \"" + sd.initial_state + "\";\n")
    s.write("    }\n\n")

    s.write("    virtual std::vector<std::pair<std::string, std::string > > getLatchedConnections() const {\n")
    s.write("        return std::vector<std::pair<std::string, std::string > > ({\n")
    for lc in sd.latched_components:
        s.write("                std::make_pair(std::string(\"" + lc[0] + "\"), std::string(\"" + lc[1] + "\")),\n")
    s.write("            });\n")
    s.write("    }\n\n")

    s.write("    virtual int getInputDataWaitCycles() const {\n")
    s.write("        return " + str(sd.no_input_wait_cycles) + ";\n")
    s.write("    }\n\n")

    s.write("    // this method is not RT-safe\n")
    s.write("    virtual std::string getErrorReasonStr(common_behavior::AbstractConditionCauseConstPtr error_reason) const {\n")
    s.write("        ErrorCauseConstPtr r = boost::dynamic_pointer_cast<const ErrorCause >(error_reason);\n")
    s.write("        return " + package + "_types::getErrorReasonStr(r);\n")
    s.write("    }\n\n")

    s.write("    // this method is not RT-safe\n")
    s.write("    virtual common_behavior::AbstractConditionCausePtr getErrorReasonSample() const {\n")
    s.write("        ErrorCausePtr ptr(new ErrorCause());\n")
    s.write("        return boost::dynamic_pointer_cast<common_behavior::AbstractConditionCause >( ptr );\n")
    s.write("    }\n\n")

    s.write("    virtual void iterationEnd() {\n")
    if sd.trigger_gazebo:
        s.write("        singleStep_();\n")
    else:
        s.write("        // do nothing\n")
    s.write("    }\n\n")

    s.write("protected:\n")
    for p in sd.ports_in:
        s.write("    " + p.type_pkg + "::" + p.type_name + " " + p.short_name + "_prev_;\n")
        s.write("    int " + p.short_name + "_no_data_counter_;\n")
        s.write("    RTT::InputPort<" + p.type_pkg + "::" + p.type_name + " > port_" + p.short_name + "_in_;\n")
        s.write("    RTT::OutputPort<" + p.type_pkg + "::" + p.type_name + " > port_" + p.short_name + "_out_;\n")

    s.write("\n    RTT::InputPort<bool > port_no_data_trigger_in__;\n")

    s.write("\n    RTT::TaskContext* owner_;\n")
    if sd.trigger_gazebo:
        s.write("    RTT::OperationCaller<void()> singleStep_;\n")

    s.write("};\n\n")

    s.write("std::string getErrorReasonStr(ErrorCauseConstPtr err) {\n")
    s.write("    std::string result;\n")
    for e in sd.errors:
        s.write("    result += (err->getBit(" + e + "_bit)?\"" + e + " \":\"\");\n")
    s.write("    return result;\n")
    s.write("}\n\n")

    s.write("};  // namespace " + package + "_types\n\n")

    s.write("ORO_SERVICE_NAMED_PLUGIN(" + package + "_types::" + package + "_Master, \"" + package + "_master\");\n")


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
