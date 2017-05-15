#!/usr/bin/python
import sys
import copy
import os

from cStringIO import StringIO
import argparse

import xml.dom.minidom as minidom

class Data:
    def __init__(self):
        self.bit_len = None
        self.name = None
        self.data_type = None

class Slave:
    def __init__(self):
        self.name = None
        self.tx = []
        self.rx = []

def eprint(s):
    sys.stderr.write(s + '\n')
    sys.stderr.flush()

def generate_boost_serialization(package, ec_config_file, msg_output_dir):
    """
    Generate a boost::serialization header

    @param msg_path: The path to the .msg file
    @type msg_path: str
    """

    eprint("generating Test.msg")

    s = StringIO()
    s.write("# autogenerated by rtt_subsystem_ports/create_msgs_from_ec_config.py\n")
    s.write("# do not modify this file\n\n")

    dom = minidom.parse(ec_config_file)

    EtherCATConfig = dom.getElementsByTagName("EtherCATConfig")

    Config = EtherCATConfig[0].getElementsByTagName("Config")

    Slaves = Config[0].getElementsByTagName("Slave")
    slave_list = []
    for slave in Slaves:
        sl = Slave()
        Info = slave.getElementsByTagName("Info")
        if len(Info) == 0:
            sl.name = "UNKNOWN"
        elif len(Info[0].getElementsByTagName("Name")) == 0:
            sl.name = "UNKNOWN"
        else:
            Name = Info[0].getElementsByTagName("Name")[0]
            sl.name = Name.childNodes[0].data

#        s.write("# slave " + sl.name + "\n")
        eprint("slave " + sl.name)

        ProcessData = slave.getElementsByTagName("ProcessData")
        if len(ProcessData) > 0:
            TxPdo = ProcessData[0].getElementsByTagName("TxPdo")
            if len(TxPdo) > 0:
                Entry = TxPdo[0].getElementsByTagName("Entry")
                for e in Entry:
                    d = Data()
                    d.bit_len = e.getElementsByTagName("BitLen")[0].childNodes[0].data
                    if len(e.getElementsByTagName("Name")) > 0:
                        d.name = e.getElementsByTagName("Name")[0].childNodes[0].data
                        d.data_type = e.getElementsByTagName("DataType")[0].childNodes[0].data
                    sl.tx.append(d)
#                    s.write("#    TX: " + d.data_type + " " + d.name + "\n")

            RxPdo = ProcessData[0].getElementsByTagName("RxPdo")
            if len(RxPdo) > 0:
                Entry = RxPdo[0].getElementsByTagName("Entry")
                for e in Entry:
                    d = Data()
                    d.bit_len = e.getElementsByTagName("BitLen")[0].childNodes[0].data
                    if len(e.getElementsByTagName("Name")) > 0:
                        d.name = e.getElementsByTagName("Name")[0].childNodes[0].data
                        d.data_type = e.getElementsByTagName("DataType")[0].childNodes[0].data
                    sl.rx.append(d)
#                    s.write("#    RX: " + d.data_type + " " + d.name + "\n")
        slave_list.append(sl)
    
#    mcd = dom.getElementsByTagName("mcd")
#    if len(mcd) != 1:
#        return (ss_history, ret_period)



    for sl in slave_list:
        s.write("# slave " + sl.name + "\n")
        for tx in sl.tx:
            if tx.name:
                s.write("#    TX: " + tx.data_type + " " + tx.name + "\n")
        for rx in sl.rx:
            if rx.name:
                s.write("#    RX: " + rx.data_type + " " + rx.name + "\n")
        s.write("\n")

    output_msg = msg_output_dir + "/Test.msg"

    (output_dir,filename) = os.path.split(output_msg)
    try:
        os.makedirs(output_dir)
    except OSError, e:
        pass

    f = open(output_msg, 'w')
    print >> f, s.getvalue()

    s.close()


def create_boost_headers(argv, stdout, stderr):
    parser = argparse.ArgumentParser(description='Generate boost serialization header for ROS message.')
    parser.add_argument('pkg',metavar='PKG',type=str, nargs=1,help='The package name.')
    parser.add_argument('ec_config_file',metavar='EC_CONF',type=str, nargs=1,help='EC definition file.')
    parser.add_argument('msg_output_dir',metavar='MSG_OUT',type=str, nargs=1,help='msg destination dir.')

    args = parser.parse_args()

    print args.pkg[0], args.ec_config_file[0], args.msg_output_dir[0]

    generate_boost_serialization(args.pkg[0], args.ec_config_file[0], args.msg_output_dir[0])

if __name__ == "__main__":
    try:
        create_boost_headers(sys.argv, sys.stdout, sys.stderr)
    except Exception, e:
        sys.stderr.write("Failed to generate boost headers: " + str(e))
        raise
        #sys.exit(1)

