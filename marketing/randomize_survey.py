__author__ = 'mattdyer'

import random
import sys

#start here when the script is launched
if (__name__ == '__main__'):
    priceOptions = {'$100k':1, '$250k':1, '$500k':1}
    imageOptions = {'Average':1, 'Superior':1}
    magnetOptions = {'Low / Mid-Field':1, 'High / Very High-Field':1}
    sizeOptions = {'Portable':1,'Fixed':1}
    formOptions = {'Open':1, 'Closed':1}
    cloudOptions = {'Integrated':1, 'Not Integrated':1}
    teleradiologyOptions = {'Integrated':1, 'Not Integrated':1}
    brandOptions = {'Name Brand':1, 'Not Name Brand':1}
    numOptions = 25
    options = {}

    while numOptions > 0:
        #grab random combo
        price = random.choice(priceOptions.keys())
        image = random.choice(imageOptions.keys())
        magnet = random.choice(magnetOptions.keys())
        size = random.choice(sizeOptions.keys())
        form = random.choice(formOptions.keys())
        cloud = random.choice(cloudOptions.keys())
        teleradiology = random.choice(teleradiologyOptions.keys())
        brand = random.choice(brandOptions.keys())

        key = '%s%s%s%s%s%s%s%s' % (price, image, magnet, size, form, cloud, teleradiology, brand)

        if key not in options:
            options[key] = 1
            numOptions -= 1

            #print it out
            print 'Price: %s' % price
            print 'Image Quality: %s' % image
            print 'Magnet Strength: %s' % magnet
            print 'Size: %s' % size
            print 'Form: %s' % form
            print 'Cloud: %s' % cloud
            print 'Teleradiology: %s' % teleradiology
            print 'Brand: %s' % brand
            print '\n\n'

            #assume base case of $100k, average, low/mid, portable, open, integrated, integrated, and name brand
            #print out the array so we can get things into Excel easily
            sys.stdout.write('%i' % numOptions)

            if price == '$250k':
                sys.stdout.write('\t1')
            else:
                sys.stdout.write('\t0')

            if price == '$500k':
                sys.stdout.write('\t1')
            else:
                sys.stdout.write('\t0')

            if image == 'Superior':
                sys.stdout.write('\t1')
            else:
                sys.stdout.write('\t0')

            if magnet == 'High / Very High-Field':
                sys.stdout.write('\t1')
            else:
                sys.stdout.write('\t0')

            if size == 'Fixed':
                sys.stdout.write('\t1')
            else:
                sys.stdout.write('\t0')

            if form == 'Closed':
                sys.stdout.write('\t1')
            else:
                sys.stdout.write('\t0')

            if cloud == 'Not Integrated':
                sys.stdout.write('\t1')
            else:
                sys.stdout.write('\t0')

            if teleradiology == 'Not Integrated':
                sys.stdout.write('\t1')
            else:
                sys.stdout.write('\t0')

            if brand == 'Not Name Brand':
                sys.stdout.write('\t1\n\n')
            else:
                sys.stdout.write('\t0\n\n')