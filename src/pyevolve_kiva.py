from pyevolve import G1DList
from pyevolve import GSimpleGA
from pyevolve import Mutators
from pyevolve import Initializators
from pyevolve import GAllele
from pyevolve import Consts
from pyevolve import DBAdapters
from pyevolve import Selectors
from kiva_runner import KivaRunner
from logger.logger import Logger


# Custom Initializer for kiva
def G1DListInitializatorAlleleKiva(genome, **args):
	""" Allele initialization function of G1DList
	"""
	global runner
	# initialize with default parameters
	genome.genomeList = runner.getParameters()
	log.debug("Initialized Allele List with: %s" % runner.getParameters())

def eval_func(chromosome):
	global runner
	params = []
	for value in chromosome:
		params.append(value)
	log.debug("Testing params: %s" % params)
	runner.setParameters(params)
	runner.run(60 * 5, 5)	# 5 min timeout, 5 restarts max
	score = runner.getFitness()
	log.debug("Fitness: %s" % score)
	return score

def run_main():
	# Global runner instance that will also be used by eval_func
	global runner
	global log

	# "Settings"
	working_dir = '../work'
	log_dir     = '../log'
	compare_values = '../ext/Detalierte Mechanismus.csv'
	log = Logger()
	log.setLogLevel('debug')

	# load parameter format defines from parameters.py
	import parameters
	pformat = parameters.parameter_format

	# load KivaRunner
	l = Logger()
	l.setLogLevel('info')
	runner = KivaRunner(working_dir, log_dir, compare_values, pformat, l)
	if runner.error:
		return

	# Genome instance
	setOfAlleles = GAllele.GAlleles()

	# loop trough parameter format to create correct alleles
	for p in pformat:
		minimum = p[2]
		maximum = p[3]
		# log.debug("maximum: %s, minimum: %s" % (maximum, minimum))
		a = GAllele.GAlleleRange(minimum, maximum, not isinstance(minimum, int))
		setOfAlleles.add(a)

	genome = G1DList.G1DList(len(pformat))
	genome.setParams(allele=setOfAlleles)

	# The evaluator function (objective function)
	genome.evaluator.set(eval_func)

	# This mutator and initializator will take care of
	# initializing valid individuals based on the allele set
	# that we have defined before
	genome.mutator.set(Mutators.G1DListMutatorAllele)
	# genome.initializator.set(G1DListInitializatorAlleleKiva)
	genome.initializator.set(Initializators.G1DListInitializatorAllele)

	# Genetic Algorithm Instance
	ga = GSimpleGA.GSimpleGA(genome)
	ga.setGenerations(10)
	ga.setPopulationSize(20)
	ga.setMinimax(Consts.minimaxType["minimize"])
	# ga.setCrossoverRate(1.0)
	ga.setMutationRate(0.1)
	ga.selector.set(Selectors.GRouletteWheel)

	sqlite_adapter = DBAdapters.DBSQLite(identify="ex1", resetDB=True)
	ga.setDBAdapter(sqlite_adapter)

	# Do the evolution, with stats dump
	# frequency of 10 generations
	ga.evolve(freq_stats=1)

	# Best individual
	best = ga.bestIndividual()
	print "\nBest individual score: %.2f" % (best.getRawScore(),)
	print best


if __name__ == "__main__":
	run_main()
