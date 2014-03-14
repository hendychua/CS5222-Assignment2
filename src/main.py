import sys
import logging
from logging import StreamHandler

log = logging.getLogger(__name__)

NOT_PROCESSED = 0
PROCESSING = 1
PROCESSED = 2
FETCHED = 3

class GraphNode(object):
    
    def __init__(self, index, latency):
        self.index = index
        self.latency = latency
        self.producers = set()
        self.consumers = set()
        self.status = NOT_PROCESSED
        self.latencies_left = latency
    
    def __repr__(self):
        string = ""
        string += "Instruction %s: latency=%s, producers=%s, consumers=%s, status=%s\n"% \
                    (self.index, self.latency, [p.index for p in self.producers],
                    [c.index for c in self.consumers], self.status)
        return string
        
def main(instructions_file="", fetch_size=-1, num_execution_units=-1):
    # -1 for infinite
    
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
            
                # register renaming. look up the source regs in the table and see if any prev instructions writing to it
                if registers_table[s1_reg] is not READY:
                    parent_node = all_nodes[registers_table[s1_reg]]
                    new_node.producers.add(parent_node)
                    parent_node.consumers.add(new_node)
                if registers_table[s2_reg] is not READY:
                    parent_node = all_nodes[registers_table[s2_reg]]
                    new_node.producers.add(parent_node)
                    parent_node.consumers.add(new_node)
                # destinatio register renaming
                registers_table[dest_reg] = index
            
                all_nodes.append(new_node)
    log.info(all_nodes)
    
    cycles = 0 # final answer to be printed
    execution_units_taken = 0
    instructions_in_window = 0
    while not all(n.status==PROCESSED for n in all_nodes):
        cycles += 1
        
        log.info("fetching")
        # fetch instructions into window (simulating fetch, decode, issue)
        if fetch_size != -1:
            available_window_size = fetch_size - instructions_in_window
        else:
            available_window_size = -1
        current_fetched_instructions = 0
        if available_window_size > 0 or available_window_size == -1:
            for inode in all_nodes:
                if inode.status == NOT_PROCESSED:
                    log.debug("fetching inode %s in cycle %s"%(inode.index, cycles))
                    inode.status = FETCHED
                    current_fetched_instructions += 1
                    instructions_in_window += 1
                    if current_fetched_instructions == available_window_size:
                        break

        log.info("moving to execute state")
        # move those that are fetched to execution state for those that are able to
        for inode in all_nodes:
            log.debug("execution_units_taken: %s. num_execution_units: %s"%(execution_units_taken, num_execution_units))
            if execution_units_taken < num_execution_units or num_execution_units==-1:
                if inode.status == FETCHED:
                    if not inode.producers or \
                        all(n.status==PROCESSED for n in inode.producers):
                        # no true dependencies with previous instructions or parent instructions have completed
                        log.debug("moving to PROCESSING state for inode %s in cycle %s"%(inode.index, cycles))
                        inode.status = PROCESSING
                        execution_units_taken += 1
                        instructions_in_window -= 1
        
        log.info("executing")
        # execute those that are able to
        for inode in all_nodes:
            if inode.status == PROCESSING:
                log.debug("reducing latencies_left for inode %s"%inode.index)
                inode.latencies_left -= 1
                inode.status = PROCESSED if inode.latencies_left==0 else PROCESSING
                if inode.status == PROCESSED:
                    execution_units_taken -= 1

    print cycles

if __name__ == "__main__":
    root = logging.getLogger()

    handler = StreamHandler()
    handler.setFormatter(logging.Formatter("(%(levelname)s) %(name)s: %(msg)s"))

    root.setLevel(logging.ERROR)
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