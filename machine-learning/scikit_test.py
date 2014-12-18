__author__ = 'mattdyer'

import numpy as np
import pylab as pl

from optparse import OptionParser
from scipy import interp
from sklearn.datasets import load_iris
from sklearn.cross_validation import ShuffleSplit
from sklearn.metrics import roc_curve, auc, confusion_matrix
from sklearn import svm, linear_model
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.linear_model import RandomizedLogisticRegression
from openpyxl import load_workbook

__author__ = 'mattdyer'

## Run a machine learning model
# @param data The data array object
# @param modelType The type of model to run (Linear SVM, Logistic Regression)
def runModel(data, modelType):
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
            ('classification', linear_model.LogisticRegression(C=1e5, random_state=0))
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
    pl.legend(loc="lower right")

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
    parser.add_option('-m', '--matrx', dest='matrix', help='The matrix file from QC / VC pipeline')
    (options, args) = parser.parse_args()

    # Load data
    iris = load_iris()
    X = iris.data
    Y = iris.target
    #print X
    #print Y

    X, Y = X[Y != 2], Y[Y != 2]

    #add some noise
    nSamples, nFeatures = X.shape
    X = np.c_[X, np.random.randn(nSamples, 100 * nFeatures)]

    #create the cross validation datasets
    data = ShuffleSplit(len(X), n_iter=int(options.folds), test_size=float(options.test), indices=False, random_state=0)

    #run the SVM classifier
    #runModel(data, 'Linear SVM')
    runModel(data, 'Logistic Regression')
    #pl.subplot(2, 2, i + 1)

    #plot the graph
    pl.show()




