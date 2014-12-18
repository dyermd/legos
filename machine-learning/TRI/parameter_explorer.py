__author__ = 'mattdyer'

import numpy as np
import pylab as pl
import re
import logging
import xlsxwriter
from sample import Sample
from sklearn.cross_validation import ShuffleSplit

from sklearn.metrics import roc_curve, auc
from sklearn.neighbors import KNeighborsClassifier
from scipy import interp
from optparse import OptionParser
from sklearn import svm, linear_model
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import BernoulliRBM
from sklearn.pipeline import Pipeline

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
    #print features
    #print labels
    logging.info('Starting model exploration')
    return(features, labels)

## Run a machine learning model
# @param X The feature data matrix
# @param Y The class data matrix
# @param data The cross validation data matrix
# @param modelType The type of model to run (Linear SVM, Logistic Regression)
# @param crossValidations The number of cross validations to run
# @param outDir The output directory
def runModel(X, Y, data, modelType, crossValidations, outDir):
    #see if we wanted logistic regression
    if(modelType == 'Logistic Regression'):
        cs = [0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000, 5000, 10000, 50000, 100000, 1000000]

        for c in cs:
            classifier = linear_model.LogisticRegression(C=c, random_state=0)
            analyze(X, Y, data, classifier, '%s, C=%f' % (modelType, c), outDir)
    #svm
    elif modelType == "SVM":
        cs = [0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000, 5000, 10000, 50000, 100000, 1000000]
        gammas = [0, 0.0001, 0.001, 0.01, 0.1]
        degrees = [2,3,4,5]

        for c in cs:
            classifier = svm.SVC(kernel='linear', probability=True, random_state=0, C=c)
            analyze(X, Y, data, classifier, '%s, C=%f' % ('Linear SVM', c), outDir)

            for gamma in gammas:
                classifier = svm.SVC(kernel='rbf', probability=True, random_state=0, C=c, gamma=gamma)
                analyze(X, Y, data, classifier, '%s, C=%f, G=%f' % ('Radial SVM', c, gamma), outDir)

                for degree in degrees:
                    classifier = svm.SVC(kernel='poly', probability=True, random_state=0, C=c, gamma=gamma, degree=degree)
                    analyze(X, Y, data, classifier, '%s, C=%f, G=%f, D=%i' % ('Poly SVM', c, gamma, degree), outDir)
    elif modelType == "Random Forest":
        estimators = [10, 15, 20, 25]
        features1 = [0.10, 0.20, 0.40]
        features2 = ['sqrt', 'log2']

        for estimator in estimators:
            for feature in features1:
                classifier = RandomForestClassifier(n_estimators=estimator, max_features=feature, random_state=0)
                analyze(X, Y, data, classifier, '%s, E=%i, F=%f' % ('Random Forest', estimator, feature), outDir)

            for feature in features2:
                classifier = RandomForestClassifier(n_estimators=estimator, max_features=feature, random_state=0)
                analyze(X, Y, data, classifier, '%s, E=%i, F=%s' % ('Random Forest', estimator, feature), outDir)

            classifier = RandomForestClassifier(n_estimators=estimator, max_features=None, random_state=0)
            analyze(X, Y, data, classifier, '%s, E=%i, F=%s' % ('Random Forest', estimator, 'All'), outDir)

    elif modelType == "kNN":
        neighbors = [5, 10, 15, 20, 25]
        weights = ['uniform', 'distance']
        algorithms = ['ball_tree', 'kd_tree', 'brute']

        for neighbor in neighbors:
            for algorithm in algorithms:
                classifier = KNeighborsClassifier(n_neighbors=neighbor, algorithm=algorithm)
                analyze(X, Y, data, classifier, '%s, N=%i, A=%s' % ('kNN', neighbor, algorithm), outDir)

            for weight in weights:
                classifier = KNeighborsClassifier(n_neighbors=neighbor, weights=weight, algorithm='brute')
                analyze(X, Y, data, classifier, '%s, N=%i, W=%s, A=%s' % ('kNN', neighbor, weight, 'brute'), outDir)

    elif modelType == "Bayesian":
        classifier = GaussianNB()
        analyze(X, Y, data, classifier, '%s' % ('Naive Bayes'), outDir)
    elif modelType == "Neural Network":
        cs = [0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000, 5000, 10000, 50000, 100000, 1000000]
        components = [0, 2, 8, 16, 64, 128, 256]
        rates = [0.0001, 0.001, 0.01, 0.1, 1]
        sizes = [10, 20, 30, 40, 50]
        iterations = [10, 20, 30, 40, 50]

        for component in components:
            for rate in rates:
                for size in sizes:
                    for iteration in iterations:
                        for c in cs:
                            classifier = Pipeline([
                                ('learning', BernoulliRBM(n_components=component, learning_rate=rate, batch_size=size, n_iter=iteration, random_state=0)),
                                ('classification', linear_model.LogisticRegression(C=c))
                            ])
                            analyze(X, Y, data, classifier, '%s, C=%f, Co=%i, R=%f, S=%i, I=%i' % ('Neural Network', c, component, rate, size, iteration), outDir)

## Run the tests and generate the graphs
# @param X The feature data matrix
# @param Y The class data matrix
# @param data The cross validation data matrix
# @param classifier The classifier
# @param label The label used in the graph
# @param outDir The output directory
def analyze(X, Y, data, classifier, label, outDir):
    #store the means for our ROC curve
    meanTPRate = 0.0
    meanFPRate = np.linspace(0, 1, 100)

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
    pl.title('ROC Curve (%s)' % (label))
    pl.legend(loc="lower right")

    pl.savefig('%s/%s.png' % (outDir, label))
    pl.close()
    logging.info("%s\t%f" % (label, meanAUC))

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the logger
    logging.basicConfig(level=logging.INFO)

    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-f', '--folds', dest='folds', help='The cross-fold validations')
    parser.add_option('-m', '--matrix', dest='matrix', help='The matrix file from QC / VC pipeline')
    parser.add_option('-t', '--test', dest='test', help='The fraction of data that goes into the test set (i.e. withheld from training set)')
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    (options, args) = parser.parse_args()

    # Load data first
    X, Y = loadData(options.matrix, options.output)
    data = ShuffleSplit(len(X), n_iter=int(options.folds), test_size=float(options.test), indices=False, random_state=0)

    #run the space search
    #runModel(X, Y, data, 'Logistic Regression', options.folds, options.output)
    #runModel(X, Y, data, 'SVM', options.folds, options.output)
    #runModel(X, Y, data, 'Random Forest', options.folds, options.output)
    #runModel(X, Y, data, 'kNN', options.folds, options.output)
    #runModel(X, Y, data, 'Bayesian', options.folds, options.output)
    runModel(X, Y, data, 'Neural Network', options.folds, options.output)





