# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# pylint: disable=C0103

"""

Script to update node status in the db.

This script takes a tokenserver config file, uses it to load the assignment
backend, and then writes the updated node status into the db.

"""

import os
import logging
import optparse

import tokenserver.scripts
from tokenserver.assignment import INodeAssignment


logger = logging.getLogger("tokenserver.scripts.update_node")


def update_node(config_file, service, node, **kwds):
    """Update details of a node."""
    logger.info("Updating node %s for service %s", node, service)
    logger.debug("Value: %r", kwds)
    logger.debug("Using config file %r", config_file)
    config = tokenserver.scripts.load_configurator(config_file)
    config.begin()
    try:
        backend = config.registry.getUtility(INodeAssignment)
        backend.update_node(service, node, **kwds)
    except Exception:  # pylint: disable=W0703
        logger.exception("Error while updating node")
        return False
    else:
        logger.info("Finished updating node %s", node)
        return True
    finally:
        config.end()


def main(args=None):
    """Main entry-point for running this script.

    This function parses command-line arguments and passes them on
    to the update_node() function.
    """
    usage = "usage: %prog [options] config_file service node_name"
    descr = "Update node details in the tokenserver database"
    parser = optparse.OptionParser(usage=usage, description=descr)
    parser.add_option("", "--capacity", type="int",
                      help="How many user slots the node has overall")
    parser.add_option("", "--available", type="int",
                      help="How many user slots the node has available")
    parser.add_option("", "--current-load", type="int",
                      help="How many user slots the node has occupied")
    parser.add_option("", "--downed", action="store_true",
                      help="Mark the node as down in the db")
    parser.add_option("", "--backoff", action="store_true",
                      help="Mark the node as backed-off in the db")
    parser.add_option("-v", "--verbose", action="count", dest="verbosity",
                      help="Control verbosity of log messages")

    opts, args = parser.parse_args(args)
    if len(args) != 3:
        parser.print_usage()
        return 1

    tokenserver.scripts.configure_script_logging(opts)

    config_file = os.path.abspath(args[0])
    service = args[1]
    node_name = args[2]

    kwds = {}
    if opts.capacity is not None:
        kwds["capacity"] = opts.capacity
    if opts.available is not None:
        kwds["available"] = opts.available
    if opts.current_load is not None:
        kwds["current_load"] = opts.current_load
    if opts.backoff is not None:
        kwds["backoff"] = opts.backoff
    if opts.downed is not None:
        kwds["downed"] = opts.downed

    update_node(config_file, service, node_name, **kwds)
    return 0


if __name__ == "__main__":
    tokenserver.scripts.run_script(main)
