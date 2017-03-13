import xml.dom.minidom as minidom

def str_to_bool(s):
    if s.upper() == 'TRUE':
        return True
    if s.upper() == 'FALSE':
        return False
    raise ValueError("Wrong boolean value: " + s)

def str_to_side(s):
    result = s.lower()
    if result != "top" and result != "bottom":
        raise ValueError("Wrong value of \'side\' attribute: " + s)
    return result

class InputPort:
    def __init__(self, name, type, side, ipc, short_name, period_min=None, period_avg=None, period_max=None):
        self.name = name
        self.short_name = short_name
        type_s = type.split("::")
        if len(type_s) != 2:
            raise Exception('in', 'wrong type attribute of <ports> <in> tag: ' + type + ', should be \'package::typename\"')
        self.type_pkg = type_s[0]
        self.type_name = type_s[1]
        self.side = str_to_side(side)
        self.ipc = str_to_bool(ipc)

        if period_min:
            self.event = True
            self.period_min = float(period_min)
            self.period_avg = float(period_avg)
            self.period_max = float(period_max)
        else:
            self.event = False
            self.period_min = None
            self.period_avg = None
            self.period_max = None

class OutputPort:
    def __init__(self, name, type, side, ipc):
        self.name = name
        type_s = type.split("::")
        if len(type_s) != 2:
            raise Exception('in', 'wrong type attribute of <ports> <out> tag: ' + type + ', should be \'package::typename\"')
        self.type_pkg = type_s[0]
        self.type_name = type_s[1]
        self.side = str_to_side(side)
        self.ipc = str_to_bool(ipc)

class SubsystemDefinition:
    def __init__(self):
        self.ports_in = []
        self.ports_out = []
        self.errors = []
        self.states = []
        self.initial_state = []
        self.period = None
        self.use_ros_sim_clock = False
        self.trigger_gazebo = False
        self.use_sim_clock = False
        self.no_input_wait_cycles = 0
        self.latched_components = []

def parseSubsystemXml(xml_str):
    dom = minidom.parseString(xml_str)
    subsystem_definition = dom.getElementsByTagName("subsystem_definition")
    if len(subsystem_definition) != 1:
        raise Exception('subsystem_definition', 'subsystem_definition is missing')
    ports = subsystem_definition[0].getElementsByTagName("ports")
    if len(ports) != 1:
        raise Exception('ports', 'wrong number of <ports> tags, should be 1')

    sd = SubsystemDefinition()

    ports_in = ports[0].getElementsByTagName('in')
    for p_in in ports_in:
        trigger = p_in.getElementsByTagName('trigger')
        if len(trigger) == 1:
            sd.ports_in.append( InputPort(p_in.getAttribute("name"), p_in.getAttribute("type"),
                p_in.getAttribute("side"), p_in.getAttribute("ipc"), p_in.getAttribute("short_name"),
                trigger[0].getAttribute("min"), trigger[0].getAttribute("avg"), trigger[0].getAttribute("max")) )
        elif len(trigger) == 0:
            sd.ports_in.append( InputPort(p_in.getAttribute("name"), p_in.getAttribute("type"), p_in.getAttribute("side"), p_in.getAttribute("ipc"), p_in.getAttribute("short_name")) )
        else:
            raise Exception('ports in trigger', 'wrong number of <ports> <in> <trigger> tags, should be 0 or 1')

    ports_out = ports[0].getElementsByTagName('out')
    for p_out in ports_out:
        sd.ports_out.append( OutputPort(p_out.getAttribute("name"), p_out.getAttribute("type"), p_in.getAttribute("side"), p_out.getAttribute("ipc")) )
        
    #
    # <errors>
    #
    errors = subsystem_definition[0].getElementsByTagName("errors")
    if len(errors) != 1:
        raise Exception('errors', 'wrong number of <errors> tags, should be 1')
    err = errors[0].getElementsByTagName("err")
    for e in err:
        sd.errors.append( e.getAttribute("name") )

    states = subsystem_definition[0].getElementsByTagName("states")
    if len(states) != 1:
        raise Exception('states', 'wrong number of <states> tags, should be 1')
    state = states[0].getElementsByTagName("state")
    for s in state:
        sd.states.append( s.getAttribute("name") )
    initial_state = states[0].getElementsByTagName("initial_state")
    if len(initial_state) != 1:
        raise Exception('initial_state', 'wrong number of <initial_state> tags, should be 1')
    sd.initial_state = initial_state[0].getAttribute("name")

    #
    # <activity>
    #
    activity = subsystem_definition[0].getElementsByTagName("activity")
    if len(activity) == 1:
        period = activity[0].getAttribute("period")
        if not period:
            raise Exception('period', '<activity> tag must contain period attribute')
        sd.period = float(period)

    #
    # <simulation>
    #
    simulation = subsystem_definition[0].getElementsByTagName("simulation")
    if len(simulation) == 1:
        use_ros_sim_clock = simulation[0].getAttribute("use_ros_sim_clock")
        if not use_ros_sim_clock:
            raise Exception('use_ros_sim_clock', '<simulation> tag must contain \'use_ros_sim_clock\' attribute')
        sd.use_ros_sim_clock = str_to_bool(use_ros_sim_clock)

        use_sim_clock = simulation[0].getAttribute("use_sim_clock")
        if not use_sim_clock:
            raise Exception('use_sim_clock', '<simulation> tag must contain \'use_sim_clock\' attribute')
        sd.use_sim_clock = str_to_bool(use_sim_clock)

        trigger_gazebo = simulation[0].getAttribute("trigger_gazebo")
        if trigger_gazebo:
            sd.trigger_gazebo = str_to_bool(trigger_gazebo)
    elif len(simulation) > 1:
        raise Exception('simulation', 'wrong number of <simulation> tags, must be 0 or 1')

    #
    # <no_input_wait>
    #
    no_input_wait = subsystem_definition[0].getElementsByTagName("no_input_wait")
    if len(no_input_wait) == 1:
        cycles = no_input_wait[0].getAttribute("cycles")
        if not cycles:
            raise Exception('no_input_wait cycles', '<no_input_wait> tag must contain cycles attribute')
        sd.no_input_wait_cycles = int(cycles)
    elif len(no_input_wait) > 1:
        raise Exception('no_input_wait', 'wrong number of <no_input_wait> tags, must be 0 or 1')

    #
    # <latched_connections>
    #
    latched_connections = subsystem_definition[0].getElementsByTagName("latched_connections")
    if len(latched_connections) == 1:
        components = latched_connections[0].getElementsByTagName("components")
        for c in components:
            first = c.getAttribute("first")
            second = c.getAttribute("second")
            if not first:
                raise Exception('latched_connections components first', '<latched_connections> <components> tag must contain \'first\' attribute')
            if not second:
                raise Exception('latched_connections components first', '<latched_connections> <components> tag must contain \'second\' attribute')
            sd.latched_components.append( (first, second) )
    elif len(latched_connections) > 1:
        raise Exception('latched_connections', 'wrong number of <latched_connections> tags, must be 0 or 1')

    return sd

