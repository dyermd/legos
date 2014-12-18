#generate all the plots for the market project
from optparse import OptionParser
import matplotlib.pyplot as plt


__author__ = 'mattdyer'


# add labels to a plot
# @param points The plot object
# @param axis The axis object
def autolabel(points, axis, data):
    # attach some text labels
    for i, point in enumerate(points):
        height = float(point.get_height())

        axis.text(point.get_x()+point.get_width()/2., 1.05*height, '%.1f'%data[i],
                ha='center', va='bottom')

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    (options, args) = parser.parse_args()


    ############
    #Figure X - histogram
    ############

    fix, ax1 = plt.subplots()
    data = [4.30 , 5.37 , 11.11 , 13.25 , 13.25 , 18.99 , 21.14 , 21.14 , 21.49 , 22.57 , 23.64 , 23.64 , 24.00 , 25.08 , 25.79 , 30.09 , 35.11 , 36.18 , 36.90 , 36.90 , 39.76 , 40.12 , 40.12 , 40.12 , 42.27 , 44.06 , 46.93 , 47.29 , 47.64 , 48.36 , 49.08 , 51.23 , 51.94 , 52.66 , 53.02 , 58.75 , 59.11 , 59.11 , 60.18 , 60.54 , 61.97 , 62.33 , 64.48 , 67.71 , 69.85 , 72.00 , 72.00 , 74.51 , 74.87 , 77.02 , 77.38 , 78.09 , 80.24 , 80.96 , 83.11 , 86.69 , 87.77 , 88.48 , 90.63 , 90.99 , 91.71 , 92.78 , 92.78 , 94.21 , 94.93 , 97.08 , 97.80 , 97.80 , 101.74 , 103.53 , 103.89 , 116.78 , 117.50 , 117.86 , 121.44 , 121.44 , 123.95 , 150.81 , 151.89 , 152.96 , 161.56 , 164.78 , 169.80 , 174.82 , 193.08 , 195.23 , 227.47 , 248.61 , 112.84, 135.05, 142.57, 176.25, 179.47, 183.05, 193.80, 195.95, 207.41, 208.13, 239.65, 270.82, 279.42, 290.16, 312.37]
    ax1.hist(data, color='b', alpha=0.4)
    ax1.set_xlabel('Technical Fee ($)')
    ax1.set_ylabel('CPT Codes')
    plt.savefig('%s/figureX.png' % (options.output))


    #plt.show()