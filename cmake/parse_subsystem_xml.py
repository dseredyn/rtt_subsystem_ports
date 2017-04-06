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

class Trigger(object):
    def __init__(self, trigger_type):
        self.trigger_type = trigger_type

class TriggerOnNewData(Trigger):
    def __init__(self, xml):
        super(TriggerOnNewData, self).__init__("new_data_on_buffer")
        self.name = xml.getAttribute("name")
        self.min = float(xml.getAttribute("min"))

class TriggerOnNoData(Trigger):
    def __init__(self, xml):
        super(TriggerOnNoData, self).__init__("no_data_on_buffer")
        self.name = xml.getAttribute("name")
        self.first_timeout = float(xml.getAttribute("first_timeout"))
        self.next_timeout = float(xml.getAttribute("next_timeout"))
        self.first_timeout_sim = float(xml.getAttribute("first_timeout_sim"))

class TriggerOnPeriod(Trigger):
    def __init__(self, xml):
        super(TriggerOnPeriod, self).__init__("period")
        self.value = float(xml.getAttribute("value"))

class TriggerMethods:
    def parse(self, xml):
        new_data_on_buffer = xml.getElementsByTagName('new_data_on_buffer')
        no_data_on_buffer = xml.getElementsByTagName('no_data_on_buffer')
        period = xml.getElementsByTagName('period')

        if not (len(period) == 0 or len(period) == 1):
            raise Exception('period', 'wrong number of <period> tags in <trigger_methods>, should be 0 or 1')

        if len(new_data_on_buffer) + len(no_data_on_buffer) + len(period) == 0:
            raise Exception('<trigger_methods>', 'at least one trigger method should be specified')

        for m in new_data_on_buffer:
            if not self.new_data:
                self.new_data = []
            self.new_data.append( TriggerOnNewData(m) )

        for m in no_data_on_buffer:
            if not self.no_data:
                self.no_data = []
            self.no_data.append( TriggerOnNoData(m) )

        if len(period) == 1:
            self.period = TriggerOnPeriod(period[0])

    def __init__(self, xml=None):
        self.new_data = None
        self.no_data = None
        self.period = None
        if xml:
            self.parse(xml)

    def onNewData(self, alias=None):
        if not self.new_data:
            return None
        if not alias:
            return self.new_data
        for t in self.new_data:
            if t.name == alias:
                return t
        return None

    def onNoData(self, alias=None):
        if not self.no_data:
            return None
        if not alias:
            return self.no_data
        for t in self.no_data:
            if t.name == alias:
                return t
        return None

    def onPeriod(self):
        return self.period

class SubsystemDefinition:
    def __init__(self):
        self.ports_in = []
        self.ports_out = []
        self.trigger_methods = None
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

    def parseTriggerMethods(self, xml):
        self.trigger_methods = TriggerMethods(xml)

    def parse(self, xml):
        # <buffers>
        buffers = xml.getElementsByTagName("buffers")
        if len(buffers) != 1:
            raise Exception('buffers', 'wrong number of <buffers> tags, should be 1')
        self.parseBuffers(buffers[0])

        # <trigger>
        trigger_methods = xml.getElementsByTagName("trigger_methods")
        if len(trigger_methods) != 1:
            raise Exception('trigger_methods', 'wrong number of <trigger_methods> tags, should be 1')
        self.parseTriggerMethods(trigger_methods[0])
            
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

