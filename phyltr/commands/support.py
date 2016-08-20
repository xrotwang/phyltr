"""Usage:
    phyltr support [<options>] [<files>]

Annotate a treestream with clade support probabilities, and optionally save clade support information to a file

OPTIONS:

    -s, --sort
        Reorder tree stream to print trees in order from highest to lowest
        product of clade credibilities.

    -o, --output
        Filename to save a clade credibility report to

    -f, --frequency
        Minimum clade frequency to include in output (default 0.0, i.e. all
        clades are included)

    files
        A whitespace-separated list of filenames to read treestreams from.
        Use a filename of "-" to read from stdin.  If no filenames are
        specified, the treestream will be read from stdin.
"""

import fileinput

import dendropy

from phyltr.utils.treestream_io import read_tree, write_tree
import phyltr.utils.cladeprob
import phyltr.utils.phyoptparse as optparse

def run():

    # Parse options
    parser = optparse.OptionParser(__doc__)
    parser.add_option('-s', '--sort', action="store_true", dest="sort", default=False)
    parser.add_option("-o", "--output", action="store", dest="filename",
        help="save clades to FILE", metavar="FILE")
    parser.add_option('-f', '--frequency', type="float", dest="frequency",
            default=1.0, help='Minimum clade frequency to report.')
    options, files = parser.parse_args()

    # Read trees and compute clade probabilities
    trees = []
    cp = phyltr.utils.cladeprob.CladeProbabilities()
    for line in fileinput.input(files):
        t = read_tree(line)
        trees.append(t)
        cp.add_tree(t)
    cp.compute_probabilities()

    # Save clade probabilities
    if options.filename:
        save_clades(cp, options.filename, options.frequency)

    # Annotate trees
    for t in trees:
        cp.annotate_tree(t)

    # Sort
    if options.sort:
        trees = [(cp.get_tree_prob(t),t) for t in trees]
        trees.sort()
        trees.reverse()
        trees = [t for (p,t) in trees]

    # Output
    for t in trees:
        write_tree(t)

    # Done
    return 0

def save_clades(cp, filename, threshold):
    clade_probs = [(cp.clade_probs[c], c) for c in cp.clade_probs]
    if threshold < 1.0:
        clade_probs = [(p, c) for (p, c) in clade_probs if p >= threshold]
    # Sort by clade string, ignoring case...
    clade_probs.sort(key=lambda x:x[1].lower())
    # ...then by clade probability
    # (this results in a list sorted by probability and then name)
    clade_probs.sort(key=lambda x:x[0],reverse=True)

    fp = open(filename, "w")
    for p, c in clade_probs:
        fp.write("%f: [%s]\n" % (p, c))
    fp.close()
