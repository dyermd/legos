#generate all the plots for the market project
from optparse import OptionParser
import matplotlib.pyplot as plt
#import cartopy.crs as ccrs
import matplotlib as mpl
#import cartopy.io.shapereader as shpreader
import numpy as np

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
    #Figure 1 - histogram of cpt
    ############

    fix, ax1 = plt.subplots()
    data = [2.87 , 3.58 , 7.52 , 10.03 , 10.03 , 12.18 , 12.54 , 12.90 , 15.40 , 15.40 , 15.76 , 17.91 , 18.63 , 19.34 , 19.34 , 20.06 , 20.06 , 20.42 , 20.78 , 20.78 , 21.85 , 22.21 , 22.57 , 22.93 , 23.28 , 25.08 , 25.08 , 25.43 , 25.43 , 25.79 , 27.58 , 27.94 , 27.94 , 28.30 , 28.66 , 29.02 , 29.37 , 29.37 , 29.73 , 30.09 , 30.45 , 30.81 , 31.52 , 31.88 , 32.24 , 32.24 , 32.60 , 32.60 , 32.60 , 32.60 , 32.96 , 33.67 , 34.03 , 34.03 , 34.03 , 34.03 , 34.75 , 34.75 , 35.11 , 35.11 , 35.82 , 36.18 , 36.90 , 36.90 , 37.26 , 37.61 , 37.61 , 38.33 , 38.69 , 39.41 , 40.12 , 40.48 , 41.20 , 41.91 , 42.27 , 43.35 , 44.06 , 45.85 , 49.08 , 49.79 , 49.79 , 50.15 , 50.51 , 51.58 , 53.73 , 54.45 , 55.17 , 57.32 , 59.11 , 59.82 , 60.18 , 60.18 , 60.54 , 61.62 , 63.05 , 64.48 , 64.48 , 65.91 , 65.91 , 68.42 , 70.93 , 72.36 , 73.08 , 79.53 , 83.83 , 86.33 , 90.63 , 90.99 , 90.99 , 95.29 , 96.72 , 98.87 , 99.23 , 106.04 , 106.39 , 113.92 , 140.43 , 147.23]
    ax1.hist(data, color='b', alpha=0.4)
    ax1.set_xlabel('Profession Fee ($)')
    ax1.set_ylabel('CPT Codes')
    plt.savefig('%s/figure1.png' % (options.output))

    ############
    #Figure 2 - infection point ultrasound
    ############

    fix, ax1 = plt.subplots()
    labels = [2000,'','','','',2005,'','','','',2010,'','','','',2015,'','','','',2020,'','','','',2025,'','','','',2030]
    dataNormal = [ 55.01 , 87.69 , 124.30 , 165.24 , 210.94 , 261.90 , 314.66 , 369.26 , 425.70 , 484.00 , 544.15 , 605.40 , 667.57 , 731.05 , 796.26 , 863.68 , 933.82 , 1007.26 , 1084.74 , 1167.10 , 1255.15 , 1349.73 , 1451.65 , 1561.71 , 1680.67 , 1809.27 , 1948.16 , 2097.93 , 2259.12 , 2432.20 , 2617.56 ]
    dataBNI = [ None , None , None , None , None , None , None , None , None , None , None , None , None , None , None , None , 1165.77 , 1250.49 , 1422.29 , 1733.67 , 2245.95 , 2955.75 , 3934.34 , 5251.54 , 6958.51 , 9082.53 , 11555.52 , 14150.97 , 16589.61 , 18778.97 , 20876.74 ]
    xPos = np.arange(len(labels))
    ax1.plot(dataNormal, alpha=0.4, color='b', linewidth=2, label='Portable Ultrasound')
    ax1.plot(dataBNI, alpha=0.4, color='r', linewidth=2, label='Portable Ultrasound with Butterfly')
    ax1.set_ylabel('Revenue ($Millions)')
    ax1.set_xlabel('Year')
    plt.title('Ultrasound Teleradiology Market')
    plt.xticks(xPos, labels)
    plt.legend(loc='upper left')
    plt.savefig('%s/figure2.png' % (options.output))

    plt.show()