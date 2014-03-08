import sys
import logging
from logging import StreamHandler

log = logging.getLogger(__name__)

NOT_PROCESSED = 0
PROCESSING = 1
PROCESSED = 2

class GraphNode(object):
    
    def __init__(self, index, latency):
        self.index = index
        self.latency = latency
        self.producers = set()
        self.consumers = set()
        self.status = NOT_PROCESSED
        self.latencies_left = latency
        self.max_path_from_me = None
    
    def __repr__(self):
        string = ""
        string += "Instruction %s: latency=%s, producers=%s, consumers=%s, status=%s\n"% \
                    (self.index, self.latency, [p.index for p in self.producers],
                    [c.index for c in self.consumers], self.status)
        return string

def get_critical_path(node):
    log.debug(node.index)
    if not node.consumers:
        node.max_path_from_me = node.latency
        return node.max_path_from_me
    else:
        all_paths = []
        for consumer in node.consumers:
            if consumer.max_path_from_me:
                all_paths.append(node.latency + consumer.max_path_from_me)
            else:
                all_paths.append(node.latency + get_critical_path(consumer))
        node.max_path_from_me = max(all_paths)
        return node.max_path_from_me
        
def main(instructions_file="", fetch_size=-1, num_execution_units=-1):
    log.info("instructions_file: %s"%instructions_file)
    log.info("fetch_size: %s, num_execution_units: %s"%(fetch_size, num_execution_units))
    
    READY = True
    registers_table = dict((x,READY) for x in xrange(32)) #registers 0-31
    
    all_nodes = []
    with open(instructions_file, 'r') as file_interator:
        for index,line in enumerate(file_interator):
            log.debug("line: %s"%line.strip())
            if line.strip():
                tmp = line.strip().split(",")
                dest_reg, s1_reg = (int(x) for x in tmp[0].split("="))
                s2_reg, latency = (int(x) for x in tmp[1].split(":"))
                new_node = GraphNode(index, latency)
            
                # register renaming
                if registers_table[s1_reg] is not READY:
                    parent_node = all_nodes[registers_table[s1_reg]]
                    new_node.producers.add(parent_node)
                    parent_node.consumers.add(new_node)
                if registers_table[s2_reg] is not READY:
                    parent_node = all_nodes[registers_table[s2_reg]]
                    new_node.producers.add(parent_node)
                    parent_node.consumers.add(new_node)
                registers_table[dest_reg] = index
            
                all_nodes.append(new_node)
    log.info(all_nodes)
    
    if num_execution_units == -1 and fetch_size == -1:
        # Part (A)
        dependency_graph_heads = []
        for node in all_nodes:
            if not node.producers:
                dependency_graph_heads.append(node)
        log.debug("dependency_graph_heads: %s"%dependency_graph_heads)
        log.debug("num heads: %s"%len(dependency_graph_heads))
        
        # if no restriction on both execution units and fetch size
        # then the optimal cycles will be the critical path of the dependency graph
        latencies = []
        for i,head in enumerate(dependency_graph_heads):
            log.debug("i=%s"%i)
            latencies.append(get_critical_path(head))
        print max(latencies)
    
    else:
        # Part (B) and (C)
        cycles = 0 # final answer
        instructions_processing = 0
        while not all(n.status==PROCESSED for n in all_nodes):
            cycles += 1
            instructions_fetch_in_this_cycle = 0
            if instructions_processing < num_execution_units or num_execution_units==-1:
                for inode in all_nodes:
                    if inode.status not in (PROCESSED, PROCESSING):
                        if not inode.producers or \
                            all(n.status==PROCESSED for n in inode.producers):
                            log.debug("inode %s"%inode.index)
                            inode.status = PROCESSING
                            log.info("fetched instruction %s in cycle %s."%(inode.index, cycles))
                            instructions_processing += 1
                            instructions_fetch_in_this_cycle += 1
                    if instructions_fetch_in_this_cycle == fetch_size or \
                        instructions_processing == num_execution_units:
                        log.info("cycle %s. instructions_fetch_in_this_cycle: %s."%(cycles, instructions_fetch_in_this_cycle))
                        break

            for inode in all_nodes:
                if inode.status == PROCESSING:
                    inode.latencies_left -= 1
                    inode.status = PROCESSED if inode.latencies_left==0 else PROCESSING
                    if inode.status == PROCESSED:
                        instructions_processing -= 1
        print cycles

if __name__ == "__main__":
    root = logging.getLogger()

    handler = StreamHandler()
    handler.setFormatter(logging.Formatter("(%(levelname)s) %(name)s: %(msg)s"))

    root.setLevel(logging.INFO)
    root.addHandler(handler)
    
    # -1 for infinite amount
    if len(sys.argv) < 2:
        log.error("Bro, you've gotta at least provide me the filename ya?")
    else:
        if len(sys.argv) == 2:
            main(instructions_file=sys.argv[1], fetch_size=-1, num_execution_units=-1)
    
        elif len(sys.argv) == 3:
            fetch_size = int(sys.argv[2])
            main(instructions_file=sys.argv[1], fetch_size=fetch_size, num_execution_units=-1)
    
        elif len(sys.argv) == 4:
            fetch_size = int(sys.argv[2])
            num_execution_units = int(sys.argv[3])
            main(instructions_file=sys.argv[1], fetch_size=fetch_size, num_execution_units=num_execution_units)