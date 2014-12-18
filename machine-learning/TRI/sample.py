## @package Sample
#
# This class is responsible for managing a sample object

import unittest
import logging

__author__ = 'mattdyer'

class Sample:
    ## The constructor
    # @param self The object pointer
    # @param name The name of the gene
    def __init__(self, name):
        #set up the new object
        self.__name = name

        #try to infer class from sample name
        if self.__name.startswith('control') or self.__name.startswith('old'):
            self.setClass(0)
        elif self.__name.startswith('case'):
            self.setClass(1)
        else:
            self.__classLabel = None

        self.__variants = {}
        self.__genes = {}

    ## Set the class
    # @param self The object pointer
    # @param classLabel The class label, 0 (control) or 1 (case)
    def setClass(self, classLabel):
        if classLabel == 0 or classLabel == 1:
            self.__classLabel = classLabel
        else:
            logging.warning('Invalid class label provided, setting to 0')
            self.__classLabel = 0

    ## add a variant
    # @param self The object pointer
    # @param geneName The gene name
    # @param referenceBase The reference base
    # @param variantBase The variant base
    # @param position The position of the variant
    # @param frequency The frequency of the variant
    def addVariant(self, geneName, referenceBase, variantBase, position, frequency):
        #store the gene name as having a variant
        self.__genes[geneName] = 1

        #add the variant
        key ='%s_%s_%s_%s' % (geneName, position, referenceBase, variantBase)
        self.__variants[key] = float(frequency)

    ## see if it has a variant
    # @param self The object pointer
    # @param geneName The gene name
    # @param referenceBase The reference base
    # @param variantBase The variant base
    # @param position The position of the variant
    # @returns True / false
    def hasVariant(self, geneName, referenceBase, variantBase, position):
        key ='%s_%s_%s_%s' % (geneName, position, referenceBase, variantBase)

        #see if we have the key
        return(key in self.__variants)

    ## get the variant frequency
    # @param self The object pointer
    # @param geneName The gene name
    # @param referenceBase The reference base
    # @param variantBase The variant base
    # @param position The position of the variant
    # @returns The frequency
    def getVariantFrequency(self, geneName, referenceBase, variantBase, position):
        key ='%s_%s_%s_%s' % (geneName, position, referenceBase, variantBase)

        if(self.hasVariant(geneName, referenceBase, variantBase, position)):
            return self.__variants[key]
        else:
            logging.warning('Tried to access variant that does not exist in sample')
            return None

    ## see if variant in gene
    # @param self The object pointer
    # @param geneName The gene name
    # @returns True / false
    def hasGene(self, geneName):
        return(geneName in self.__genes)

    ## get the sample name
    # @param self The object pointer
    # @returns The sample name
    def getSampleName(self):
        return(self.__name)

    ## get the class label
    # @param self The object pointer
    # @returns The class label
    def getClassLabel(self):
        return(self.__classLabel)

    ## get the dictionary of variants
    # @param self The object pointer
    # @returns The dictionary of variants
    def getVariants(self):
        return(self.__variants)

    ## get the dictionary of genes
    # @param self The object pointer
    # @returns The dictionary of genes
    def getGenes(self):
        return(self.__genes)

## @package SampleTest
#
# This class is responsible for unit testing the sample class
class SampleTest(unittest.TestCase):
    #set up a dummy gene object
    sample = Sample("control")
    sample.addVariant('gene', 'A', 'T', '100', '0.50')

    def test_sample_name(self):
        self.assertEqual(self.sample.getSampleName(), "control")

    def test_class_label(self):
        self.assertEqual(self.sample.getClassLabel(), 0)

    def test_has_variant(self):
        self.assertEqual(self.sample.hasVariant('gene', 'A', 'T', '100'), True)
        self.assertEqual(self.sample.hasVariant('gene', 'A', 'T', '200'), False)

    def test_has_gene(self):
        self.assertEqual(self.sample.hasGene('gene'), True)
        self.assertEqual(self.sample.hasGene('gene2'), False)

    def test_frequency(self):
        self.assertEqual(self.sample.getVariantFrequency('gene', 'A', 'T', '100'), 0.50)

#if run directly from command-line, just execute test cases
if (__name__ == "__main__"):
    unittest.main()
