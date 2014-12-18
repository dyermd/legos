__author__ = 'mattdyer'

import numpy as np
import pylab as pl
import re
import logging
import xlsxwriter
from sample import Sample

from optparse import OptionParser
from scipy import interp
from sklearn.datasets import load_iris
from sklearn.cross_validation import ShuffleSplit
from sklearn.metrics import roc_curve, auc, confusion_matrix
from sklearn import svm, linear_model
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.linear_model import RandomizedLogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import BernoulliRBM

__author__ = 'mattdyer'

## Load the data from our matrix file
# @param matrixFile The matrix file
# @param outDir The output directory
# @returns Two numpy arrays of the feature vectors (X) and class labels (Y)
def loadData(matrixFile, outDir):
    #open the file and parse the contents
    logging.info('Parsing datamatrix')
    file = open(matrixFile, 'r')

    #store a few things for later
    headers = []
    sampleSummary = Sample('all')
    samples = {}

    #loop over the file
    for line in file.readlines():
        #remove the return
        line = line.rstrip('\n')

        #tokeninze the line
        tokens = line.split('\t')

        #if it is the first line we can just store the headers
        if line.startswith('GeneName'):
            headers = tokens

        #else we need to process the data
        else:
            sampleName = tokens[0]
            #print sampleName

            #create my sample
            sample = Sample(sampleName)

            #now lets start processing everything
            for num, variantInfo in enumerate(tokens[1:]):
                #grab the header info (we shouldn't be doing this for each sample, need to fix)
                gene, refpos = headers[num + 1].split('_')
                reference, position = re.findall(r"[^\W\d_]+|\d+", refpos)
                #print '%i %s %s %s' % (num, gene, reference, position)

                #now lets parse the variant info
                #if LOW_DEPTH, then skip
                if not variantInfo.startswith('LOW_DEPTH'):
                    variantInfoTokens = re.findall(r"[-+]?\d*\.\d+|\d+|\w+", variantInfo) #variantInfo.split('/')

                    #simple case is where there is just one alternate allele
                    if len(variantInfoTokens) == 3:
                        #base case
                        #reference
                        sample.addVariant(gene, reference, reference, position, 1.0 - float(variantInfoTokens[2]))
                        sampleSummary.addVariant(gene, reference, reference, position, 1.0 - float(variantInfoTokens[2]))

                        #variant
                        sample.addVariant(gene, reference, variantInfoTokens[1], position, float(variantInfoTokens[2]))
                        sampleSummary.addVariant(gene, reference, variantInfoTokens[1], position, float(variantInfoTokens[2]))

                    elif len(variantInfoTokens) == 6:
                        #need to handle when there are two alternate alleles
                        #reference
                        sample.addVariant(gene, reference, reference, position, 1.0 - float(variantInfoTokens[4]) - float(variantInfoTokens[5]))
                        sampleSummary.addVariant(gene, reference, reference, position, 1.0 - float(variantInfoTokens[4]) - float(variantInfoTokens[5]))

                        #variant 1
                        sample.addVariant(gene, reference, variantInfoTokens[1], position, float(variantInfoTokens[4]))
                        sampleSummary.addVariant(gene, reference, variantInfoTokens[1], position, float(variantInfoTokens[4]))

                        #variant 2
                        sample.addVariant(gene, reference, variantInfoTokens[2], position, float(variantInfoTokens[5]))
                        sampleSummary.addVariant(gene, reference, variantInfoTokens[2], position, float(variantInfoTokens[5]))
                    elif len(variantInfoTokens) == 2:
                        #this means there was a deletion
                        #reference
                        sample.addVariant(gene, reference, reference, position, 1.0 - float(variantInfoTokens[1]))
                        sampleSummary.addVariant(gene, reference, reference, position, 1.0 - float(variantInfoTokens[1]))

                        #deletion
                        sample.addVariant(gene, reference, '-', position, float(variantInfoTokens[1]))
                        sampleSummary.addVariant(gene, reference, '-', position, float(variantInfoTokens[1]))
                    else:
                        #this really shoudln't happen
                        print variantInfoTokens
                        logging.warning('Sample with more than two alternate alleles - %s %s' % (sampleName, variantInfo))

            #now add the sample
            samples[sampleName] = sample

    #close the file
    file.close()

    #now lets build our feature vectors, for now it will be all the variants and all the genes
    logging.info('Building feature vectors')

    #dump the array to a spreadsheet for debugging
    spreadsheet = xlsxwriter.Workbook('%s/features.xlsx' % outDir)
    featureWorksheet = spreadsheet.add_worksheet('Features')

    #set up our huge feature array and class label vectors. features is
    features = np.zeros((len(samples), len(sampleSummary.getVariants()) + len(sampleSummary.getGenes())))
    labels = np.zeros((len(samples)))

    #now let's populate our matrix
    for sampleNumber, sample in enumerate(sorted(samples)):
        sample = samples[sample]
        labels[sampleNumber] = sample.getClassLabel()

        featureWorksheet.write(sampleNumber+1, 0, sample.getSampleName())
        featureWorksheet.write(sampleNumber+1, 1, sample.getClassLabel())

        #first start with the variants
        for featureNumber, variant in enumerate(sorted(sampleSummary.getVariants())):
            geneName, position, referenceBase, variantBase = variant.split('_')
            featureWorksheet.write(0, featureNumber+2, variant)

            if(sample.hasVariant(geneName, referenceBase, variantBase, position)):
                #add frequency to array
                features[sampleNumber][featureNumber] = sample.getVariantFrequency(geneName, referenceBase, variantBase, position)
                featureWorksheet.write(sampleNumber+1, featureNumber+2, sample.getVariantFrequency(geneName, referenceBase, variantBase, position))
            else:
                featureWorksheet.write(sampleNumber+1, featureNumber+2, 0)

        #now at the gene level
        for featureNumber, gene in enumerate(sorted(sampleSummary.getGenes())):
            featureWorksheet.write(0, featureNumber+len(sampleSummary.getVariants())+1, gene)

            if(sample.hasGene(gene)):
                features[sampleNumber][featureNumber + len(sampleSummary.getVariants())] = 1
                featureWorksheet.write(sampleNumber+1, featureNumber+len(sampleSummary.getVariants())+2, 1)
            else:
                featureWorksheet.write(sampleNumber+1, featureNumber+len(sampleSummary.getVariants())+2, 0)

    #close the spreadsheet
    spreadsheet.close()

    #return the matrix
    print features
    print labels
    return(features, labels)

## Run a machine learning model
# @param data The data array object
# @param modelType The type of model to run (Linear SVM, Logistic Regression)
# @param outDir The output directory
def runModel(data, modelType, outDir):
    #store the means for our ROC curve
    meanTPRate = 0.0
    meanFPRate = np.linspace(0, 1, 100)

    #initialize our classifier
    classifier = Pipeline([
        ('feature_selection', LinearSVC()),
        ('classification', svm.SVC(kernel='linear', probability=True, random_state=0))
    ])

    #see if we wanted logistic regression
    if(modelType == 'Logistic Regression'):
        classifier = Pipeline([
            ('feature_selection', LinearSVC()),
            ('classification', linear_model.LogisticRegression(C=1000, random_state=0))
        ])
    elif modelType == 'kNN':
        classifier = Pipeline([
            ('feature_selection', LinearSVC()),
            ('classification', KNeighborsClassifier(n_neighbors=10))
        ])
    elif modelType == 'Random Forest':
        classifier = RandomForestClassifier()
    elif modelType == 'Neural Network':
        #optimize on these later with GridSearchCV
        classifier = Pipeline([
            ('learning', BernoulliRBM(random_state=0)),
            ('classification', linear_model.LogisticRegression(C=6000))
        ])

    #save the confusion matricies for later
    matrices = []

    #start with the subplot
    pl.subplots()

    #now lets analyze the data
    for i, (train, test) in enumerate(data):
        #grab the data sets for training and testing
        xTrain, xTest, yTrain, yTest = X[train], X[test], Y[train], Y[test]
        #print xTrain
        #print yTrain

        #train the model
        classifier.fit(xTrain, yTrain)


        #now predict on the hold out
        predictions = classifier.predict(xTest)
        probabilities = classifier.predict_proba(xTest)
        #print predictions
        #print probabilities
        #print classifier.get_params()

        #get the confusion matrix
        matrix = confusion_matrix(yTest, predictions)
        #print i
        matrices.append(matrix)

        #compute ROC and AUC
        fpr, tpr, thresholds = roc_curve(yTest, probabilities[:, 1])
        meanTPRate += interp(meanFPRate, fpr, tpr)
        meanTPRate[0] = 0.0
        rocAUC = auc(fpr,tpr)

        #now plot it out
        pl.plot(fpr, tpr, lw=1, label='ROC Iter %d (area = %0.2f)' % (i+1, rocAUC))

        #print "P: %s\nA: %s\n" % (predictions, yTest)

    #now plot the random chance line
    pl.plot([0,1], [0,1], '--', color=(0.6,0.6,0.6), label='Random Chance')

    #generate some stats for the mean plot
    meanTPRate /= len(data)
    meanTPRate[-1] = 1.0
    meanAUC = auc(meanFPRate, meanTPRate)

    #plot the average line
    pl.plot(meanFPRate, meanTPRate, 'k--', label='Mean ROC (area = %0.2f)' % (meanAUC), lw=2)

    #add some other plot parameters
    pl.xlim([-0.05, 1.05])
    pl.ylim([-0.05, 1.05])
    pl.xlabel('False Positive Rate')
    pl.ylabel('True Positive Rate')
    pl.title('ROC Curve (%s)' % (modelType))
    pl.legend(loc=4) #lower-right

    pl.savefig('%s/%s.png' % (outDir, modelType))

    #plot the confusion matrices
    #for i, (matrix) in enumerate(matrices):
        #pl.subplot(2,3,i + 1)
        #pl.xlim([0, 1.0])
        #pl.ylim([0, 1.0])
        #pl.imshow(matrix, interpolation='nearest', origin='upper')
        #pl.title('Confusion matrix')
        #pl.colorbar()
        #pl.ylabel('Reality')
        #pl.xlabel('Predicted')


#start here when the script is launched
if (__name__ == '__main__'):

    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-f', '--folds', dest='folds', help='The cross-fold validations')
    parser.add_option('-t', '--test', dest='test', help='The fraction of data that goes into the test set (i.e. withheld from training set)')
    parser.add_option('-m', '--matrix', dest='matrix', help='The matrix file from QC / VC pipeline')
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    (options, args) = parser.parse_args()

    # Load data first
    X, Y = loadData(options.matrix, options.output)

    #create the cross validation datasets
    data = ShuffleSplit(len(X), n_iter=int(options.folds), test_size=float(options.test), indices=False, random_state=0)
    print data

    #run the SVM classifier
    #runModel(data, 'kNN', options.output)
    #runModel(data, 'Random Forest', options.output)
    #runModel(data, 'Linear SVM', options.output)
    runModel(data, 'Logistic Regression', options.output)
    #runModel(data, 'Neural Network', options.output)

    #plot the graph
    pl.show()




