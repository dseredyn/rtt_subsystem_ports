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
    def parse(self, xml):
        self.alias = xml.getAttribute("alias")
        type_s = xml.getAttribute("type").split("::")
        if len(type_s) != 2:
            raise Exception('in', 'wrong type attribute of <ports> <in> tag: ' + type + ', should be \'package::typename\"')
        self.type_pkg = type_s[0]
        self.type_name = type_s[1]
        self.side = str_to_side(xml.getAttribute("side"))

        trigger = xml.getElementsByTagName('tgr')
        if len(trigger) == 1:
            self.event = True
            self.period_min = float(trigger[0].getAttribute("min"))
            self.period_avg = float(trigger[0].getAttribute("avg"))
            self.period_max = float(trigger[0].getAttribute("max"))
            self.period_sim_max = float(trigger[0].getAttribute("sim_max"))
        elif len(trigger) == 0:
            self.event = False
            self.period_min = None
            self.period_avg = None
            self.period_max = None
            self.period_sim_max = None
        else:
            raise Exception('ports in trigger', 'wrong number of <ports> <in> <trigger> tags, should be 0 or 1')

    def __init__(self, xml=None):
        if xml:
            self.parse(xml)

    def getTypeStr(self):
        return self.type_pkg + "_" + self.type_name

    def getTypeCpp(self):
        return self.type_pkg + "::" + self.type_name

class OutputPort:
    def parse(self, xml):
        self.alias = xml.getAttribute("alias")
        type_s = xml.getAttribute("type").split("::")
        if len(type_s) != 2:
            raise Exception('in', 'wrong type attribute of <ports> <out> tag: ' + type + ', should be \'package::typename\"')
        self.type_pkg = type_s[0]
        self.type_name = type_s[1]
        self.side = str_to_side(xml.getAttribute("side"))

    def __init__(self, xml=None):
        if xml:
            self.parse(xml)

    def getTypeStr(self):
        return self.type_pkg + "_" + self.type_name

    def getTypeCpp(self):
        return self.type_pkg + "::" + self.type_name

#class SubsystemState:
#    def parse(self, xml):
#        self.name = xml.getAttribute("name")
#        is_initial = xml.getAttribute("is_initial")
#        if is_initial:
#            self.is_initial = str_to_bool(is_initial)
#        else:
#            self.is_initial = False
#        self.behavior = xml.getAttribute("behavior")
#        self.init_cond = xml.getAttribute("init_cond")
#
#    def __init__(self, xml=None):
#        if xml:
#            self.parse(xml)

class SubsystemBehavior:
    def parse(self, xml):
        self.name = xml.getAttribute("name")
        is_initial = xml.getAttribute("is_initial")
        if is_initial:
            self.is_initial = str_to_bool(is_initial)
        else:
            self.is_initial = False
        self.init_cond = xml.getAttribute("init_cond")
        self.stop_cond = xml.getAttribute("stop_cond")
        self.err_cond = xml.getAttribute("err_cond")

        self.running_components = []
        for rc in xml.getElementsByTagName("running_component"):
            self.running_components.append( rc.getAttribute("name") )

        self.output_scopes = []
        for scope in xml.getElementsByTagName("scope"):
            self.output_scopes.append( scope.getAttribute("name") )

    def __init__(self, xml=None):
        if xml:
            self.parse(xml)

class Trigger:
    def parse(self, xml):
        buf = xml.getElementsByTagName('buffer')
        period = xml.getElementsByTagName('period')

        if len(buf) == 1:
            self.period_min = float(buf[0].getAttribute("min"))
            self.period_avg = float(buf[0].getAttribute("avg"))
            self.period_max = float(buf[0].getAttribute("max"))
            self.period_sim_max = float(buf[0].getAttribute("sim_max"))
            on_buf = buf[0].getElementsByTagName('on_buffer')
            if len(on_buf) == 0:
                raise Exception('on_buffer', 'wrong number of <on_buffer> tags, should be at least 1')
            self.buffer_aliases = []
            for b in on_buf:
                self.buffer_aliases.append(b.getAttribute("name"))
        elif len(period) == 1:
            self.period = float(period[0].getAttribute("p"))
        else:
            raise Exception('trigger', 'wrong number of <buffer> and <period> tags, should be exactly one of them')

    def __init__(self, xml=None):
        self.buffer_aliases = None
        self.period_min = None
        self.period_avg = None
        self.period_max = None
        self.period_sim_max = None

        self.period = None
        if xml:
            self.parse(xml)

class SubsystemDefinition:
    def __init__(self):
        self.ports_in = []
        self.ports_out = []
        self.trigger = None
        self.errors = []
        self.predicates = []
#        self.states = []
        self.behaviors = []
        self.period = None
        self.use_ros_sim_clock = False
        self.trigger_gazebo = False
        self.use_sim_clock = False
        self.no_input_wait_cycles = 0
        self.latched_components = []
        self.output_scopes = []

#    def getInitialStateName(self):
#        for s in self.states:
#            if s.is_initial:
#                return s.name
#        raise Exception('state.is_initial', 'there is no initial state')

    def getInitialBehaviorName(self):
        for b in self.behaviors:
            if b.is_initial:
                return b.name
        raise Exception('behavior.is_initial', 'there is no initial behavior')

    def parseBuffers(self, xml):
        # <in>
        for p_in in xml.getElementsByTagName('in'):
            p = InputPort(p_in)
            self.ports_in.append(p)

        # <out>
        for p_out in xml.getElementsByTagName('out'):
            p = OutputPort(p_out)
            self.ports_out.append(p)

    def parsePredicates(self, xml):
        for p in xml.getElementsByTagName("predicate"):
            self.predicates.append( p.getAttribute("name") )

    def parseOutputScopes(self, xml):
        for scope in xml.getElementsByTagName("scope"):
            self.output_scopes.append( scope.getAttribute("name") )

#    def parseStates(self, xml):
#        initial_state = None
#        for s in xml.getElementsByTagName("state"):
#            state = SubsystemState(s)
#            if state.is_initial and not initial_state:
#                initial_state = state.name
#            elif state.is_initial and initial_state:
#                raise Exception('state.is_initial', 'at least two states are marked as initial: ' + initial_state + ", " + state.name)
#            self.states.append( state )

    def parseBehaviors(self, xml):
        for b in xml.getElementsByTagName("behavior"):
            behavior = SubsystemBehavior(b)
            self.behaviors.append( behavior )

    def parseTrigger(self, xml):
        self.trigger = Trigger(xml)

    def parse(self, xml):
        # <buffers>
        buffers = xml.getElementsByTagName("buffers")
        if len(buffers) != 1:
            raise Exception('buffers', 'wrong number of <buffers> tags, should be 1')
        self.parseBuffers(buffers[0])

        # <trigger>
        trigger = xml.getElementsByTagName("trigger")
        if len(trigger) != 1:
            raise Exception('trigger', 'wrong number of <trigger> tags, should be 1')
        self.parseTrigger(trigger[0])
            
        # <errors>
        errors = xml.getElementsByTagName("errors")
        if len(errors) != 1:
            raise Exception('errors', 'wrong number of <errors> tags, should be 1')
        err = errors[0].getElementsByTagName("err")
        for e in err:
            self.errors.append( e.getAttribute("name") )

        # <predicates>
        predicates = xml.getElementsByTagName("predicates")
        if len(predicates) != 1:
            raise Exception('predicates', 'wrong number of <predicates> tags, should be 1')

        self.parsePredicates(predicates[0])

        # <predicates>
        output_scopes = xml.getElementsByTagName("output_scopes")
        if len(output_scopes) != 1:
            raise Exception('output_scopes', 'wrong number of <output_scopes> tags, should be 1')

        self.parseOutputScopes(output_scopes[0])
        if len(self.output_scopes) == 0:
            raise Exception('output_scopes', 'wrong number of <scope> tags in <output_scopes>, should be at least 1')

        # <behaviors>
        behaviors = xml.getElementsByTagName("behaviors")
        if len(behaviors) != 1:
            raise Exception('behaviors', 'wrong number of <behaviors> tags, should be 1')

        self.parseBehaviors(behaviors[0])

        #
        # <activity>
        #
# TODO:
        activity = xml.getElementsByTagName("activity")
        if len(activity) == 1:
            period = activity[0].getAttribute("period")
            if not period:
                raise Exception('period', '<activity> tag must contain period attribute')
            self.period = float(period)

        #
        # <simulation>
        #
        simulation = xml.getElementsByTagName("simulation")
        if len(simulation) == 1:
            use_ros_sim_clock = simulation[0].getAttribute("use_ros_sim_clock")
            if not use_ros_sim_clock:
                raise Exception('use_ros_sim_clock', '<simulation> tag must contain \'use_ros_sim_clock\' attribute')
            self.use_ros_sim_clock = str_to_bool(use_ros_sim_clock)

            use_sim_clock = simulation[0].getAttribute("use_sim_clock")
            if not use_sim_clock:
                raise Exception('use_sim_clock', '<simulation> tag must contain \'use_sim_clock\' attribute')
            self.use_sim_clock = str_to_bool(use_sim_clock)

            trigger_gazebo = simulation[0].getAttribute("trigger_gazebo")
            if trigger_gazebo:
                self.trigger_gazebo = str_to_bool(trigger_gazebo)
        elif len(simulation) > 1:
            raise Exception('simulation', 'wrong number of <simulation> tags, must be 0 or 1')

        #
        # <no_input_wait>
        #
        no_input_wait = xml.getElementsByTagName("no_input_wait")
        if len(no_input_wait) == 1:
            cycles = no_input_wait[0].getAttribute("cycles")
            if not cycles:
                raise Exception('no_input_wait cycles', '<no_input_wait> tag must contain cycles attribute')
            self.no_input_wait_cycles = int(cycles)
        elif len(no_input_wait) > 1:
            raise Exception('no_input_wait', 'wrong number of <no_input_wait> tags, must be 0 or 1')

        #
        # <latched_connections>
        #
        latched_connections = xml.getElementsByTagName("latched_connections")
        if len(latched_connections) == 1:
            components = latched_connections[0].getElementsByTagName("components")
            for c in components:
                first = c.getAttribute("first")
                second = c.getAttribute("second")
                if not first:
                    raise Exception('latched_connections components first', '<latched_connections> <components> tag must contain \'first\' attribute')
                if not second:
                    raise Exception('latched_connections components first', '<latched_connections> <components> tag must contain \'second\' attribute')
                self.latched_components.append( (first, second) )
        elif len(latched_connections) > 1:
            raise Exception('latched_connections', 'wrong number of <latched_connections> tags, must be 0 or 1')


def parseSubsystemXml(xml_str):
    dom = minidom.parseString(xml_str)
    subsystem_definition = dom.getElementsByTagName("subsystem_definition")
    if len(subsystem_definition) != 1:
        raise Exception('subsystem_definition', 'subsystem_definition is missing')

    sd = SubsystemDefinition()
    sd.parse(subsystem_definition[0])

    return sd

