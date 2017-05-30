#!/usr/bin/python
import sys
import copy
import os

from cStringIO import StringIO
import argparse
import errno
import math
import xml.dom.minidom as minidom

def nameToIdentifier(name):
    result = ""
    for ch in name:
        if ch.isalnum():
            result += ch
    keywords = ["and", "and_eq", "asm", "auto", "bitand", "bitor", "bool", "break", "case", "catch", "char", "char16_t", "char32_t", "class",
        "compl", "concept", "const", "constexpr", "const_cast", "continue", "decltype", "default", "delete", "do", "double",
        "dynamic_cast", "else", "enum", "explicit", "export", "extern", "false", "float", "for", "friend", "goto", "if", "import",
        "inline", "int", "long", "module", "mutable", "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator",
        "or", "or_eq", "private", "protected", "public", "register", "reinterpret_cast", "return", "short", "signed",
        "sizeof", "static", "static_cast", "struct", "switch", "template", "this", "throw", "true", "try", "typedef", "typeid",
        "typename", "union", "unsigned", "using", "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq"]
    if result in keywords:
        result = result + "_"

    return result

class ProcessImage:
    class Variable:
        def __init__(self):
            self.Name = None
            self.Comment = None
            self.DataType = None
            self.BitSize = None
            self.BitOffs = None

    class Interface:
        def __init__(self):
            self.ByteSize = None
            self.variables = None

    def __init__(self):
        self.Inputs = None
        self.Outputs = None

def parseVariable( xml ):
    v = ProcessImage.Variable()

    v.Name = str(xml.getElementsByTagName("Name")[0].childNodes[0].data)

    if len(xml.getElementsByTagName("DataType")) > 0:
        v.DataType = str(xml.getElementsByTagName("DataType")[0].childNodes[0].data)

    if len(xml.getElementsByTagName("Comment")) > 0:
        v.Comment = str(xml.getElementsByTagName("Comment")[0].childNodes[0].data)

    v.BitSize = int(xml.getElementsByTagName("BitSize")[0].childNodes[0].data)

    v.BitOffs = int(xml.getElementsByTagName("BitOffs")[0].childNodes[0].data)

    return v

def parseInterface( xml):
    byteSizeXml = xml.getElementsByTagName("ByteSize")
    i = ProcessImage.Interface()
    i.ByteSize = int(byteSizeXml[0].childNodes[0].data)

    variablesXml = xml.getElementsByTagName("Variable")

    i.variables = []
    for varXml in variablesXml:
        i.variables.append( parseVariable( varXml ) )

    return i

def parseProcessImage( xml ):
    inputsXml = xml.getElementsByTagName("Inputs")
    outputsXml = xml.getElementsByTagName("Outputs")

    pi = ProcessImage()

    pi.Inputs = parseInterface( inputsXml[0] )
    pi.Outputs = parseInterface( outputsXml[0] )

    return pi

class PdoEntry:
    def __init__(self):
        self.index = None
        self.subindex = None
        self.bit_len = None
        self.name = None
        self.data_type = None

class Pdo:
    def __init__(self):
        self.type = None
        self.name = None
        self.Index = None
        self.entries = None

class Slave:
    def __init__(self):
        self.name = None
        self.tx_pdo = []
        self.rx_pdo = []

    def hasPdo(self):
        return len(self.tx_pdo) > 0 or len(self.rx_pdo) > 0

def eprint(s):
    sys.stderr.write(s + '\n')
    sys.stderr.flush()

def parsePdo(pdo):
    p = Pdo()

    if pdo.nodeName == "TxPdo":
        p.type = "tx"
    elif pdo.nodeName == "RxPdo":
        p.type = "rx"
    else:
        raise Exception("wrong pdo type: " + pdo.nodeName)

    Index = pdo.getElementsByTagName("Index")
    p.index = Index[0].childNodes[0].data
    Name = pdo.getElementsByTagName("Name")
    p.name = Name[0].childNodes[0].data

    entries = pdo.getElementsByTagName("Entry")
    p.entries = []
    for e in entries:
        ent = PdoEntry()
        ent.index = e.getElementsByTagName("Index")[0].childNodes[0].data
        if len(e.getElementsByTagName("SubIndex")) > 0:
            ent.subindex = e.getElementsByTagName("SubIndex")[0].childNodes[0].data
        ent.bit_len = e.getElementsByTagName("BitLen")[0].childNodes[0].data
        if len(e.getElementsByTagName("Name")) > 0:
            ent.name = e.getElementsByTagName("Name")[0].childNodes[0].data
        if len(e.getElementsByTagName("DataType")) > 0:
            ent.data_type = e.getElementsByTagName("DataType")[0].childNodes[0].data
        p.entries.append(ent)
    return p
        
def parseSlave(slave):
    sl = Slave()
    Info = slave.getElementsByTagName("Info")
    if len(Info) == 0:
        sl.name = "UNKNOWN"
    elif len(Info[0].getElementsByTagName("Name")) == 0:
        sl.name = "UNKNOWN"
    else:
        Name = Info[0].getElementsByTagName("Name")[0]
        sl.name = Name.childNodes[0].data

    ProcessData = slave.getElementsByTagName("ProcessData")
    if len(ProcessData) > 0:
        TxPdo = ProcessData[0].getElementsByTagName("TxPdo")
        for pdo in TxPdo:
            p = parsePdo(pdo)
            sl.tx_pdo.append(p)

        RxPdo = ProcessData[0].getElementsByTagName("RxPdo")
        for pdo in RxPdo:
            p = parsePdo(pdo)
            sl.rx_pdo.append(p)
    return sl

class TreeNode:
    def __init__(self):
        self.parent_name = None
        self.variable = None

def generateMsgsFromProcessImage(variables, msg_output_dir, top_level_name):
    if len(variables) == 0:
        return

    map_data_types = {
        "BIT"   : "bool",
        "SINT"  : "int8",
        "USINT" : "uint8",
        "INT"   : "int16",
        "UINT"  : "uint16",
        "DINT"  : "int32",
        "UDINT" : "uint32"}

    parents = {}
    children = {}
    leafs = {}
    top_level = []
    for v in variables:
        leafs[ v.Name ] = v
        names = []
        idx = v.Name.find(".")
        if idx >= 0:
            if not v.Name[0:idx] in top_level:
                top_level.append(v.Name[0:idx])
        while idx >= 0:
            names.append(v.Name[0:idx])
            idx = v.Name.find(".", idx+1)
        names.append(v.Name)
        for i in range(len(names)-1):
            if not names[i] in children:
                children[names[i]] = []
            if not names[i+1] in children[names[i]]:
                children[names[i]].append( names[i+1] )

            if not names[i+1] in parents:
                parents[ names[i+1] ] = []
            parents[ names[i+1] ].append( names[i] )

#    eprint("leafs:")
#    for n in leafs:
#        eprint("   " + n)

    for n in children:
        if n in leafs:
            continue

        s = StringIO()
        s.write("# autogenerated by rtt_subsystem_ports/create_msgs_from_ec_config.py\n")
        s.write("# do not modify this file\n\n")

        for ch in children[n]:
            data_name = ch[ch.rfind(".")+1:]
            if ch in leafs:
                if leafs[ch].DataType in map_data_types:
                    s.write(map_data_types[leafs[ch].DataType] + " " + nameToIdentifier(data_name) + "    # subsystem_buffer{type: port}\n")
                else:
                    array_size = int(math.floor(float(leafs[ch].BitSize)/8.0))
                    s.write("byte[" + str(array_size) + "] " + nameToIdentifier(data_name) + "    # subsystem_buffer{type: port}\n")
            else:
                s.write(top_level_name + nameToIdentifier(ch) + " " + nameToIdentifier(data_name) + "    # subsystem_buffer{type: container}\n")

        msg_name = top_level_name + nameToIdentifier(n) + ".msg"

        output_msg = msg_output_dir + "/" + msg_name

        (output_dir,filename) = os.path.split(output_msg)
        try:
            os.makedirs(output_dir)
        except OSError, e:
            pass

        f = open(output_msg, 'w')
        print >> f, s.getvalue()

        s.close()



    s = StringIO()
    s.write("# autogenerated by rtt_subsystem_ports/create_msgs_from_ec_config.py\n")
    s.write("# do not modify this file\n\n")

    for ch in top_level:
        data_name = ch[ch.rfind(".")+1:]
        if ch in leafs:
            if leafs[ch].DataType in map_data_types:
                s.write(map_data_types[leafs[ch].DataType] + " data_" + nameToIdentifier(data_name) + "    # subsystem_buffer{type: port}\n")
            else:
                array_size = int(math.floor(float(leafs[ch].BitSize)/8.0))
                s.write("byte[" + str(array_size) + "] data_" + nameToIdentifier(data_name) + "    # subsystem_buffer{type: port}\n")
        else:
            s.write(top_level_name + nameToIdentifier(ch) + " data_" + nameToIdentifier(data_name) + "    # subsystem_buffer{type: container}\n")

    msg_name = top_level_name + ".msg"

    output_msg = msg_output_dir + "/" + msg_name

    (output_dir,filename) = os.path.split(output_msg)
    try:
        os.makedirs(output_dir)
    except OSError, e:
        pass

    f = open(output_msg, 'w')
    print >> f, s.getvalue()

    s.close()

def generate_msgs(package, ec_config_file, msg_output_dir, ec_msg_converter_filename, ec_msg_converter_h_filename):
    """
    Generate a boost::serialization header

    @param msg_path: The path to the .msg file
    @type msg_path: str
    """

    # Try to make the directory, but silently continue if it already exists
    try:
        os.makedirs(msg_output_dir)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

    dom = minidom.parse(ec_config_file)

    EtherCATConfig = dom.getElementsByTagName("EtherCATConfig")

    Config = EtherCATConfig[0].getElementsByTagName("Config")

    SlavesXml = Config[0].getElementsByTagName("Slave")
    slave_list = []
    for slave in SlavesXml:
        sl = parseSlave(slave)
        slave_list.append(sl)

    ProcessImageXml = Config[0].getElementsByTagName("ProcessImage")
    pi = parseProcessImage( ProcessImageXml[0] )
    
    generateMsgsFromProcessImage(pi.Inputs.variables, msg_output_dir, "EcInput")
    generateMsgsFromProcessImage(pi.Outputs.variables, msg_output_dir, "EcOutput")

    s = StringIO()
    s.write("// autogenerated by rtt_subsystem_ports/create_msgs_from_ec_config.py\n")
    s.write("// do not modify this file\n\n")

#    s.write("class abcd {\n")
#    s.write("};")

#    s.write("#include <rtt/RTT.hpp>\n")
#    s.write("#include <rtt/Component.hpp>\n")
#    s.write("#include <rtt/Logger.hpp>\n")
    s.write("#include \"" + package + "/EcInput.h\"\n")
    s.write("#include \"" + package + "/EcOutput.h\"\n\n")

#    s.write("using namespace RTT;\n\n")

    s.write("namespace " + package + " {\n")

    s.write("void convert(const EcInput& msg, boost::array<uint8_t, " + str(pi.Inputs.ByteSize) + " > &data) {\n")
    s.write("}\n")

    s.write("void convert(const boost::array<uint8_t, " + str(pi.Inputs.ByteSize) + " > &data, EcInput& msg) {\n")
    s.write("}\n")

#    s.write("class BypassComponent: public RTT::TaskContext {\n")
#    s.write("class BypassComponent {\n")
#    s.write("public:\n")
#    s.write("    explicit BypassComponent(const std::string &name)\n")
#    s.write("        : TaskContext(name, PreOperational)\n")
#    s.write("    { }\n")
#    s.write("    bool configureHook() { return true; }\n")
#    s.write("    bool startHook() { return true; }\n")
#    s.write("    void stopHook() {}\n")
#    s.write("    void updateHook() {}\n")
#    s.write("    std::string getDiag() { return \"\"; }\n")
#    s.write("};\n")

#private:
#    typedef Eigen::Matrix<double, 4, 1 > HandDofs;
#    RTT::InputPort<ArmJoints > port_cmd_rArm_t_in_;
#    velma_core_cs_ve_body_msgs::StatusSC sc_out_;
#    RTT::OutputPort<velma_core_cs_ve_body_msgs::StatusSC> port_sc_out_;
#};

#BypassComponent::BypassComponent(const std::string &name)
#    , port_cmd_lHand_hold_in_("lHand_hold_INPORT")
#{
#    this->ports()->addPort(port_cmd_lHand_hold_in_);
#
#}

#std::string BypassComponent::getDiag() {
#// this method may not be RT-safe
#    return "";
#}
    s.write("}   //namespace " + package + "\n")

#    s.write("ORO_LIST_COMPONENT_TYPE(BypassComponent)\n")


    (output_dir,filename) = os.path.split(ec_msg_converter_filename)
    try:
        os.makedirs(output_dir)
    except OSError, e:
        pass

    f = open(ec_msg_converter_filename, 'w')
    print >> f, s.getvalue()

    s.close()

    s = StringIO()
    s.write("// autogenerated by rtt_subsystem_ports/create_msgs_from_ec_config.py\n")
    s.write("// do not modify this file\n\n")

    s.write("#include \"" + package + "/EcInput.h\"\n")
    s.write("#include \"" + package + "/EcOutput.h\"\n\n")
    s.write("#include \"" + package + "/ec_msg_converter.h\"\n\n")
    s.write("namespace " + package + " {\n")

    s.write("void convert(const EcInput& msg, boost::array<uint8_t, " + str(pi.Inputs.ByteSize) + " > &data);\n")
    s.write("void convert(const boost::array<uint8_t, " + str(pi.Inputs.ByteSize) + " > &data, EcInput& msg);\n")

    s.write("}   //namespace " + package + "\n")

    (output_dir,filename) = os.path.split(ec_msg_converter_h_filename)
    try:
        os.makedirs(output_dir)
    except OSError, e:
        pass

    f = open(ec_msg_converter_h_filename, 'w')
    print >> f, s.getvalue()

    s.close()

def create_msgs(argv, stdout, stderr):
    parser = argparse.ArgumentParser(description='Generate boost serialization header for ROS message.')
    parser.add_argument('pkg',metavar='PKG',type=str, nargs=1,help='The package name.')
    parser.add_argument('ec_config_file',metavar='EC_CONF',type=str, nargs=1,help='EC definition file.')
    parser.add_argument('msg_output_dir',metavar='MSG_OUT',type=str, nargs=1,help='msg destination dir.')
    parser.add_argument('ec_msg_converter_filename',metavar='MSG_OUT',type=str, nargs=1,help='EC msg converter filename.')
    parser.add_argument('ec_msg_converter_h_filename',metavar='MSG_OUT',type=str, nargs=1,help='EC msg converter header filename.')

    args = parser.parse_args()

    print args.pkg[0], args.ec_config_file[0], args.msg_output_dir[0], args.ec_msg_converter_filename[0], args.ec_msg_converter_h_filename[0]

    generate_msgs(args.pkg[0], args.ec_config_file[0], args.msg_output_dir[0], args.ec_msg_converter_filename[0], args.ec_msg_converter_h_filename[0])

if __name__ == "__main__":
    try:
        create_msgs(sys.argv, sys.stdout, sys.stderr)
    except Exception, e:
        sys.stderr.write("Failed to generate boost headers: " + str(e))
        raise
        #sys.exit(1)

