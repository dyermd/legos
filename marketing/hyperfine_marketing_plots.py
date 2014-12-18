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
    #Figure 1: imaging markets revenue / CAGR
    ############
    '''
    fig, ax1 = plt.subplots()
    revenues = [1.5, 4.2, 4.5, 4.6, 7.3]
    labels = ['Nuclear Medicine', 'CT', 'Ultrasound', 'MRI', 'X-Ray']

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, revenues, align='center', alpha=0.4, color='b', label='Revenue')
    ax1.set_ylabel('Revenue (Billions USD)')

    #final additions and then plot
    autolabel(plot1, ax1, revenues)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure1a.png' % (options.output))
    #plt.show()

    fig, ax1 = plt.subplots()
    cagr = [5.8, 4.5, 6.2, 6.2, 5.4]

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, cagr, align='center', alpha=0.4, color='r', label='CAGR')
    ax1.set_ylabel('CAGR [2010 - 2018] (%)')

    #final additions and then plot
    autolabel(plot1, ax1, cagr)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure1b.png' % (options.output))


    ############
    #Figure 2, tripod - done in Illustrator
    ############

    ############
    #Figure 3, MRI market overview
    ############

    fig, ax1 = plt.subplots()
    revenues = [1604.6, 109.9, 638.3, 839.8, 820.9, 392.6, 227.9, 4634.0]
    labels = ['US', 'Canada', 'Japan', 'Europe', 'APAC', 'Latin Amer', 'ROW', 'Total']

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, revenues, align='center', alpha=0.4, color='b', label='Revenue')
    ax1.set_ylabel('Revenue (Millions USD)')

    #final additions and then plot
    autolabel(plot1, ax1, revenues)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure3a.png' % (options.output))
    #plt.show()

    fig, ax1 = plt.subplots()
    cagr = [5.2, 6.3, 5.1, 2.5, 11.9, 7.7, 7.5, 6.2]

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, cagr, align='center', alpha=0.4, color='r', label='CAGR')
    ax1.set_ylabel('CAGR [2010 - 2018] (%)')

    #final additions and then plot
    autolabel(plot1, ax1, cagr)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure3b.png' % (options.output))

    fig, ax1 = plt.subplots()
    ax1.axis('equal')
    data = [34.6, 2.4, 13.8, 18.1, 17.7, 8.47, 4.92]
    labels = ['US', 'Canada', 'Japan', 'Europe', 'Asia-Pacific', 'Latin America', 'Rest of World']
    pie_wedge_collection = plt.pie(data, labels=labels,autopct='%1.1f%%', startangle=90)

    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor('white')

    plt.title("MRI Market Share")
    plt.savefig('%s/figure3c.png' % (options.output))

    ############
    #Figure 4, cloud platform services
    ############

    fig, ax1 = plt.subplots()
    revenues = [77, 93, 110, 131, 155, 181, 210]
    labels = ['2010', '2011', '2012', '2013', '2014', '2015', '2016']

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, revenues, align='center', alpha=0.4, color='b', label='Revenue')
    ax1.set_ylabel('Revenue (Millions USD)')

    #final additions and then plot
    autolabel(plot1, ax1, revenues)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure4a.png' % (options.output))
    #plt.show()

    fig, ax1 = plt.subplots()
    cagr = [0, 20.8, 18.6, 18.5, 18.4, 17.2, 15.8]

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, cagr, align='center', alpha=0.4, color='r', label='CAGR')
    ax1.set_ylabel('CAGR [2011 - 2016] (%)')

    #final additions and then plot
    autolabel(plot1, ax1, cagr)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure4b.png' % (options.output))

    ############
    #Figure 5, cloud market breakdown by submarket
    ############
    plt.subplots()
    markets = ['Security Services', 'IaaS', 'SaaS', 'PaaS', 'Advertising']
    data = [
        [1,1,1,1,1,2,3],
        [3,4,6,9,13,18,24],
        [11,13,16,20,24,28,33],
        [27,29,31,36,40,45,50],
        [34,43,53,61,71,83,95]
    ]

    #set the colors
    colors = ['r', 'y', 'g', 'b', 'c']

    #plot the data
    index = np.arange(len(labels))
    offset = np.array([0.0] * len(labels))
    for row in range(len(data)):
        plt.bar(index, data[row], label=markets[row], align='center', alpha=0.4, bottom=offset, color=colors[row])
        offset += data[row]

    plt.xticks(xPos, labels)
    plt.ylabel('Revenue (Billions USD)')
    plt.legend(loc='upper left')
    plt.title('Cloud Services Submarkets')
    plt.savefig('%s/figure5a.png' % (options.output))

    plt.subplots()
    markets = ['Security\nServices', 'IaaS', 'SaaS', 'PaaS', 'Advertising', 'Cloud\nServices\nTotal']
    data = [26.7, 41.3, 19.5, 27.7, 17.0, 17.7]

    #plot the data
    index = np.arange(len(markets))
    plot = plt.barh(index, data, color='b', align='center', alpha=0.4)

    #set the individual colors now
    plot[0].set_color('r')
    plot[1].set_color('y')
    plot[2].set_color('g')
    plot[3].set_color('b')
    plot[4].set_color('c')
    plot[5].set_color('k')

    plt.yticks(xPos, markets)
    plt.xlabel('5-Year CAGR (2011-2016) (%)')
    plt.title('Cloud Services CAGR by Submarket' )
    plt.savefig('%s/figure5b.png' % (options.output))

    ############
    #Figure 6 - Teleradiology market
    ############

    fig, ax1 = plt.subplots()
    ax1.axis('equal')
    data = [63, 3, 2, 2, 2, 1, 1, 26]
    labels = ['vRad', 'US Radiology', 'Imaging on Call', 'Rays', 'TeleRad', 'Aris', 'Radisphere', 'Other']
    pie_wedge_collection = plt.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)

    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor('white')

    plt.title("Teleradiology Provider Market Share")
    plt.savefig('%s/figure6.png' % (options.output))

    ############
    #Figure 7 - CON states
    ############

    #start to build the map
    states = {
        'Arkansas':'g',
        'Connecticut':'g',
        'Hawaii':'g',
        'Kentucky':'g',
        'Maine':'g',
        'Massachusetts':'b',
        'Michigan':'g',
        'Mississippi':'b',
        'Missouri':'g',
        'New Hampshire':'g',
        'New York':'g',
        'North Carolina':'g',
        'Rhode Island':'g',
        'South Carolina':'g',
        'Tennessee':'b',
        'Vermont':'g',
        'Virginia':'g',
        'West Virginia':'g',
        'District of Columbia':'g'
    }
    plt.figure()
    statesShape = shpreader.natural_earth(resolution='110m', category='cultural', name='admin_1_states_provinces_shp')
    ax = plt.axes([0.01, 0.01, 0.98, 0.98], projection=ccrs.PlateCarree())
    ax.set_xlim([-175, -66.5])
    ax.set_ylim([15, 80])
    cmap = mpl.cm.Blues

    # finish the map

    for state in shpreader.Reader(statesShape).records():
        name = state.attributes['name']
        #print '%s\t%s' % (name, state.attributes['name_alt'])

        #see if key exists
        if name in states:
            ax.add_geometries(state.geometry, ccrs.PlateCarree(), facecolor='b', alpha=0.4, label=name)
        else:
            ax.add_geometries(state.geometry, ccrs.PlateCarree(), facecolor='#FAFAFA', label=name)

    plt.title('States with C.O.N. Policy')
    plt.savefig('%s/figure7.png' % (options.output))

    ############
    #Figure 8 - MRI by application
    ############
    fig, ax1 = plt.subplots()
    ax1.axis('equal')
    data = [31.5, 24.0, 13.6, 9.8, 8.2, 12.9]
    labels = ['Brain', 'Whole Body', 'Cardiac / Vascular', 'Interventional', 'Breast', 'Other']
    pie_wedge_collection = plt.pie(data, labels=labels,autopct='%1.1f%%', startangle=90)

    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor('white')

    plt.title("MRI Scans by Application")
    plt.savefig('%s/figure8.png' % (options.output))

    ############
    #Figure 9 - Market share by vender
    ############
    fig, ax1 = plt.subplots()
    ax1.axis('equal')
    data = [30, 30, 20, 12, 5, 3]
    labels = ['GE', 'Siemens', 'Philips', 'Toshiba', 'Hitachi', 'Other']
    pie_wedge_collection = plt.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)

    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor('white')

    plt.title("MRI Market Share")
    plt.savefig('%s/figure9.png' % (options.output))

    ############
    #Figure 10 - Value chain image
    ############

    ############
    #Figure 11 - Porter's chain image, taken from wikipedia
    ############

    ############
    #Figure 12 - org chart image, made in Illustrator
    ############

    ############
    #Figure 13 - US hospitals by size
    ############

    fig, ax1 = plt.subplots()
    hospitals = [389, 1151, 995, 1070, 596, 355, 184, 270]
    labels = ['<24', '25-49', '50-99', '100-199', '200-299', '300-399', '400-499', '>500']

    #axis 1 revenue
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, hospitals, align='center', alpha=0.4, color='b', label='Hospitals')
    ax1.set_ylabel('Number of Hospitals')
    ax1.set_xlabel('Number of Beds')
    plot1[0].set_color('b')
    plot1[1].set_color('b')
    plot1[2].set_color('b')
    plot1[3].set_color('y')
    plot1[4].set_color('y')
    plot1[5].set_color('r')
    plot1[6].set_color('r')
    plot1[7].set_color('r')

    #final additions and then plot
    autolabel(plot1, ax1, hospitals)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure13.png' % (options.output))

    ############
    #Figure 14 - world hospitals by country
    ############
    countries = {
        "Aruba":"0.012461798",
        "Andorra":"-0.101176126",
        "Afghanistan":"2.485035011",
        "Angola":"2.331864772",
        "Albania":"1.44304696",
        "United Arab Emirates":"1.970631771",
        "Argentina":"2.6174852",
        "Armenia":"1.473715517",
        "American Samoa":"-0.258336377",
        "Antigua and Barbuda":"-0.045829879",
        "Australia":"3.149878199",
        "Austria":"2.444745051",
        "Azerbaijan":"1.973894031",
        "Burundi":"2.007001926",
        "Belgium":"2.307427255",
        "Benin":"2.013825868",
        "Burkina Faso":"2.228781072",
        "Bangladesh":"3.194777786",
        "Bulgaria":"1.861242493",
        "Bahrain":"1.124559975",
        "Bahamas, The":"0.576771975",
        "Bosnia and Herzegovina":"1.583120186",
        "Belarus":"1.9761665",
        "Belize":"0.521007252",
        "Bermuda":"-0.186926318",
        "Bolivia":"2.02821326",
        "Brazil":"3.301815196",
        "Barbados":"0.454302034",
        "Brunei Darussalam":"0.620951804",
        "Bhutan":"0.877340817",
        "Botswana":"1.305597257",
        "Central African Republic":"1.664305032",
        "Canada":"2.872773297",
        "Switzerland":"2.491143119",
        "Channel Islands":"0.209563267",
        "Chile":"2.631247389",
        "China":"4.132701446",
        "Cote d'Ivoire":"2.307840043",
        "Cameroon":"2.347407284",
        "Congo, Rep.":"1.648128846",
        "Colombia":"2.684139553",
        "Comoros":"0.866238294",
        "Cabo Verde":"0.698010892",
        "Costa Rica":"1.687722077",
        "Cuba":"2.051755445",
        "Curacao":"0.18610838",
        "Cayman Islands":"-0.233326952",
        "Cyprus":"1.057348824",
        "Czech Republic":"2.408575304",
        "Germany":"3.512511175",
        "Djibouti":"0.940980414",
        "Dominica":"-0.142649408",
        "Denmark":"1.749249664",
        "Dominican Republic":"2.017190367",
        "Algeria":"2.593376838",
        "Ecuador":"2.196946174",
        "Egypt, Arab Rep.":"2.914112343",
        "Eritrea":"1.801618746",
        "Spain":"2.884200791",
        "Estonia":"1.753633913",
        "Ethiopia":"2.973593113",
        "Finland":"2.453305249",
        "Fiji":"0.945007949",
        "France":"3.440491704",
        "Faeroe Islands":"-0.305666869",
        "Micronesia, Fed. Sts.":"0.015145909",
        "Gabon":"1.2231612",
        "United Kingdom":"2.806838279",
        "Georgia":"1.650977394",
        "Ghana":"2.413376857",
        "Guinea":"2.06986001",
        "Gambia, The":"1.267003847",
        "Guinea-Bissau":"1.231534577",
        "Equatorial Guinea":"0.879103911",
        "Greece":"2.489514875",
        "Grenada":"0.024883657",
        "Greenland":"-0.248082245",
        "Guatemala":"2.189439863",
        "Guam":"0.217810201",
        "Guyana":"0.902879846",
        "Hong Kong SAR, China":"1.856577858",
        "Honduras":"1.90836104",
        "Croatia":"1.628664747",
        "Haiti":"2.013572836",
        "Hungary":"2.244468024",
        "Indonesia":"3.397706523",
        "Isle of Man":"-0.06606751",
        "India":"4.097652749",
        "Ireland":"1.998971897",
        "Iran, Islamic Rep.":"2.889005542",
        "Iraq":"2.523973645",
        "Iceland":"0.960991647",
        "Israel":"1.958611811",
        "Italy":"3.093945038",
        "Jamaica":"1.433769834",
        "Jordan":"1.810165285",
        "Japan":"3.935548811",
        "Kazakhstan":"2.231406073",
        "Kenya":"2.646929767",
        "Kyrgyz Republic":"1.757358064",
        "Cambodia":"2.179987275",
        "Kiribati":"0.01009209",
        "St. Kitts and Nevis":"-0.266072835",
        "Korea, Rep.":"3.520088646",
        "Kosovo":"1.261024834",
        "Kuwait":"1.527445834",
        "Lao PDR":"1.830571155",
        "Lebanon":"1.650053868",
        "Liberia":"1.632869828",
        "Libya":"1.792498219",
        "St. Lucia":"0.260722342",
        "Liechtenstein":"-0.432679496",
        "Sri Lanka":"2.311393565",
        "Lesotho":"1.316906112",
        "Lithuania":"1.470722207",
        "Luxembourg":"1.134288892",
        "Latvia":"1.303926829",
        "Macao SAR, China":"0.753104075",
        "St. Martin (French part)":"-0.504955458",
        "Morocco":"2.518621184",
        "Monaco":"-0.422152179",
        "Moldova":"1.551327988",
        "Madagascar":"2.360306522",
        "Maldives":"0.537848047",
        "Mexico":"3.6786061",
        "Marshall Islands":"-0.278733624",
        "Middle income":"4.696334051",
        "Macedonia, FYR":"1.323697101",
        "Mali":"2.184738264",
        "Malta":"0.626629801",
        "Myanmar":"2.726393155",
        "Montenegro":"0.793359368",
        "Mongolia":"1.45317656",
        "Northern Mariana Islands":"-0.26877397",
        "Mozambique":"2.412187486",
        "Mauritania":"1.589936204",
        "Mauritius":"1.112706526",
        "Malawi":"2.213851438",
        "Malaysia":"2.473004453",
        "Namibia":"1.362353336",
        "New Caledonia":"0.418301291",
        "Niger":"2.251182276",
        "Nigeria":"3.239588108",
        "Nicaragua":"1.783937721",
        "Netherlands":"2.447354062",
        "Norway":"1.706221772",
        "Nepal":"2.444005067",
        "New Zealand":"2.227762134",
        "Oman":"1.560198928",
        "Other small states":"2.305663498",
        "Pakistan":"3.260411517",
        "Panama":"1.587056224",
        "Peru":"2.482524908",
        "Philippines":"2.992966736",
        "Palau":"-0.679479841",
        "Papua New Guinea":"1.864585949",
        "Poland":"3.010688817",
        "Puerto Rico":"1.558118633",
        "Korea, Dem. Rep.":"2.396120504",
        "Portugal":"2.358975071",
        "Paraguay":"1.832655462",
        "French Polynesia":"0.442214722",
        "Qatar":"1.336194073",
        "Romania":"2.300238446",
        "Russian Federation":"3.15685148",
        "Rwanda":"2.071017048",
        "Saudi Arabia":"2.45982762",
        "Sudan":"2.579375465",
        "Senegal":"2.150242963",
        "Singapore":"1.732329415",
        "Solomon Islands":"0.749141652",
        "Sierra Leone":"1.784765241",
        "El Salvador":"1.802120356",
        "San Marino":"-0.502406969",
        "Somalia":"2.021006567",
        "Serbia":"1.855154122",
        "South Sudan":"2.052931335",
        "Small states":"2.469782044",
        "Sao Tome and Principe":"0.285541557",
        "Suriname":"0.731811093",
        "Slovak Republic":"2.147328389",
        "Slovenia":"1.4650325",
        "Sweden":"1.938102593",
        "Swaziland":"1.096741126",
        "Sint Maarten (Dutch part)":"-0.401329843",
        "Seychelles":"-0.049766622",
        "Syrian Arab Republic":"2.358801618",
        "Turks and Caicos Islands":"-0.480198248",
        "Chad":"2.108068007",
        "Togo":"1.833592147",
        "Thailand":"2.826142871",
        "Tajikistan":"1.914228564",
        "Turkmenistan":"1.719337254",
        "Timor-Leste":"1.071238186",
        "Tonga":"0.022523221",
        "Trinidad and Tobago":"1.127477678",
        "Tunisia":"2.036888277",
        "Turkey":"3.169798125",
        "Tuvalu":"-1.005418919",
        "Tanzania":"2.6924338",
        "Uganda":"2.574943786",
        "Ukraine":"2.657912118",
        "Uruguay":"1.532380037",
        "United States":"3.769377061",
        "Uzbekistan":"2.480597584",
        "St. Vincent and the Grenadines":"0.038910125",
        "Venezuela, RB":"2.482947964",
        "Virgin Islands (U.S.)":"0.02010013",
        "Vietnam":"2.952835531",
        "Vanuatu":"0.402713501",
        "West Bank and Gaza":"1.620084603",
        "Samoa":"0.279603073",
        "Yemen, Rep.":"2.387521181",
        "South Africa":"2.724128275",
        "Congo, Dem. Rep.":"2.829391762",
        "Zambia":"2.162523783",
        "Zimbabwe":"2.150745636"
    }

    min = 1.005
    max = 4.696
    shapeName = 'admin_0_countries'
    countriesShape = shpreader.natural_earth(resolution='110m', category='cultural', name=shapeName)
    ax = plt.axes(projection=ccrs.Robinson())
    cmap = mpl.cm.Blues

    # finish the map

    for country in shpreader.Reader(countriesShape).records():
        name = country.attributes['name_long']

        #see if key exists
        if name in countries:
            value = float(countries[name]) + min
            ax.add_geometries(country.geometry, ccrs.PlateCarree(), facecolor=cmap(value / float(max + min), 1), label=name)
        else:
            ax.add_geometries(country.geometry, ccrs.PlateCarree(), facecolor='#FAFAFA', label=name)

    plt.title('Number of Hospitals (log)')
    plt.savefig('%s/figure14a.png' % (options.output))

    countries = {
        "Aruba":"1.02911",
        "Andorra":"0.79218",
        "Afghanistan":"305.51674",
        "Angola":"214.71618",
        "Albania":"27.7362",
        "United Arab Emirates":"93.46129",
        "Argentina":"414.46246",
        "Armenia":"29.76566",
        "American Samoa":"0.55165",
        "Antigua and Barbuda":"0.89985",
        "Australia":"1412.141445",
        "Austria":"278.448608",
        "Azerbaijan":"94.16598",
        "Burundi":"101.62532",
        "Belgium":"202.9678519",
        "Benin":"103.23474",
        "Burkina Faso":"169.34839",
        "Bangladesh":"1565.94962",
        "Bulgaria":"72.65115",
        "Bahrain":"13.32171",
        "Bahamas, The":"3.77374",
        "Bosnia and Herzegovina":"38.29307",
        "Belarus":"94.66",
        "Belize":"3.319",
        "Bermuda":"0.65024",
        "Bolivia":"106.712",
        "Brazil":"2003.61925",
        "Barbados":"2.84644",
        "Brunei Darussalam":"4.17784",
        "Bhutan":"7.53947",
        "Botswana":"20.21144",
        "Central African Republic":"46.16417",
        "Canada":"746.0592109",
        "Switzerland":"309.8440199",
        "Channel Islands":"1.62018",
        "Chile":"427.8065102",
        "China":"13573.8",
        "Cote d'Ivoire":"203.16086",
        "Cameroon":"222.53959",
        "Congo, Rep.":"44.47632",
        "Colombia":"483.21405",
        "Comoros":"7.34917",
        "Cabo Verde":"4.98897",
        "Costa Rica":"48.72166",
        "Cuba":"112.65629",
        "Curacao":"1.535",
        "Cayman Islands":"0.58435",
        "Cyprus":"11.41166",
        "Czech Republic":"256.1977458",
        "Germany":"3254.701582",
        "Djibouti":"8.72932",
        "Dominica":"0.72003",
        "Denmark":"56.13706",
        "Dominican Republic":"104.03761",
        "Algeria":"392.08194",
        "Ecuador":"157.37878",
        "Egypt, Arab Rep.":"820.56378",
        "Eritrea":"63.33135",
        "Spain":"765.9506528",
        "Estonia":"56.70663972",
        "Ethiopia":"941.00756",
        "Finland":"283.9914395",
        "Fiji":"8.81065",
        "France":"2757.348782",
        "Faeroe Islands":"0.49469",
        "Micronesia, Fed. Sts.":"1.03549",
        "Gabon":"16.71711",
        "United Kingdom":"640.97085",
        "Georgia":"44.769",
        "Ghana":"259.04598",
        "Guinea":"117.45189",
        "Gambia, The":"18.49285",
        "Guinea-Bissau":"17.04255",
        "Equatorial Guinea":"7.57014",
        "Greece":"308.6845374",
        "Grenada":"1.05897",
        "Greenland":"0.56483",
        "Guatemala":"154.68203",
        "Guam":"1.65124",
        "Guyana":"7.99613",
        "Hong Kong SAR, China":"71.875",
        "Honduras":"80.97688",
        "Croatia":"42.527",
        "Haiti":"103.17461",
        "Hungary":"175.5771618",
        "Indonesia":"2498.65631",
        "Isle of Man":"0.85888",
        "India":"12521.39596",
        "Ireland":"99.76355051",
        "Iran, Islamic Rep.":"774.47168",
        "Iraq":"334.17476",
        "Iceland":"9.1409566",
        "Israel":"90.910032",
        "Italy":"1241.49518",
        "Jamaica":"27.15",
        "Jordan":"64.59",
        "Japan":"8620.824642",
        "Kazakhstan":"170.37508",
        "Kenya":"443.53691",
        "Kyrgyz Republic":"57.195",
        "Cambodia":"151.35169",
        "Kiribati":"1.02351",
        "St. Kitts and Nevis":"0.54191",
        "Korea, Rep.":"3311.987171",
        "Kosovo":"18.24",
        "Kuwait":"33.68572",
        "Lao PDR":"67.69727",
        "Lebanon":"44.6739",
        "Liberia":"42.94077",
        "Libya":"62.01521",
        "St. Lucia":"1.82273",
        "Liechtenstein":"0.36925",
        "Sri Lanka":"204.83",
        "Lesotho":"20.74465",
        "Lithuania":"29.56121",
        "Luxembourg":"13.62350616",
        "Latvia":"20.13385",
        "Macao SAR, China":"5.66375",
        "St. Martin (French part)":"0.31264",
        "Morocco":"330.0815",
        "Monaco":"0.37831",
        "Moldova":"35.59",
        "Madagascar":"229.24851",
        "Maldives":"3.45023",
        "Mexico":"4770.963561",
        "Marshall Islands":"0.52634",
        "Middle income":"49697.44376",
        "Macedonia, FYR":"21.07158",
        "Mali":"153.0165",
        "Malta":"4.23282",
        "Myanmar":"532.59018",
        "Montenegro":"6.21383",
        "Mongolia":"28.39073",
        "Northern Mariana Islands":"0.53855",
        "Mozambique":"258.33752",
        "Mauritania":"38.8988",
        "Mauritius":"12.96303",
        "Malawi":"163.62567",
        "Malaysia":"297.16965",
        "Namibia":"23.03315",
        "New Caledonia":"2.62",
        "Niger":"178.3127",
        "Nigeria":"1736.15345",
        "Nicaragua":"60.80478",
        "Netherlands":"280.1264141",
        "Norway":"50.8419",
        "Nepal":"277.97457",
        "New Zealand":"168.951532",
        "Oman":"36.32444",
        "Other small states":"202.14523",
        "Pakistan":"1821.42594",
        "Panama":"38.6417",
        "Peru":"303.75603",
        "Philippines":"983.93574",
        "Palau":"0.20918",
        "Papua New Guinea":"73.21262",
        "Poland":"1024.917285",
        "Puerto Rico":"36.15086",
        "Korea, Dem. Rep.":"248.9548",
        "Portugal":"228.5467611",
        "Paraguay":"68.02295",
        "French Polynesia":"2.76831",
        "Qatar":"21.68673",
        "Romania":"199.63581",
        "Russian Federation":"1434.99861",
        "Rwanda":"117.76522",
        "Saudi Arabia":"288.2887",
        "Sudan":"379.64306",
        "Senegal":"141.3328",
        "Singapore":"53.992",
        "Solomon Islands":"5.61231",
        "Sierra Leone":"60.92075",
        "El Salvador":"63.40454",
        "San Marino":"0.31448",
        "Somalia":"104.95583",
        "Serbia":"71.63976",
        "South Sudan":"112.96173",
        "Small states":"294.97285",
        "Sao Tome and Principe":"1.92993",
        "Suriname":"5.39276",
        "Slovak Republic":"140.3874834",
        "Slovenia":"29.17645344",
        "Sweden":"86.71667008",
        "Swaziland":"12.49514",
        "Sint Maarten (Dutch part)":"0.39689",
        "Seychelles":"0.89173",
        "Syrian Arab Republic":"228.4555",
        "Turks and Caicos Islands":"0.33098",
        "Chad":"128.25314",
        "Togo":"68.16982",
        "Thailand":"670.10502",
        "Tajikistan":"82.07834",
        "Turkmenistan":"52.40072",
        "Timor-Leste":"11.78252",
        "Tonga":"1.05323",
        "Trinidad and Tobago":"13.41151",
        "Tunisia":"108.865",
        "Turkey":"1478.421007",
        "Tuvalu":"0.09876",
        "Tanzania":"492.53126",
        "Uganda":"375.78876",
        "Ukraine":"454.896",
        "Uruguay":"34.07062",
        "United States":"5879.996405",
        "Uzbekistan":"302.411",
        "St. Vincent and the Grenadines":"1.09373",
        "Venezuela, RB":"304.05207",
        "Virgin Islands (U.S.)":"1.04737",
        "Vietnam":"897.089",
        "Vanuatu":"2.52763",
        "West Bank and Gaza":"41.69506",
        "Samoa":"1.90372",
        "Yemen, Rep.":"244.07381",
        "South Africa":"529.81991",
        "Congo, Dem. Rep.":"675.13677",
        "Zambia":"145.3864",
        "Zimbabwe":"141.49648"
    }

    max = 13574
    shapeName = 'admin_0_countries'
    countriesShape = shpreader.natural_earth(resolution='110m', category='cultural', name=shapeName)
    ax = plt.axes(projection=ccrs.Robinson())
    cmap = mpl.cm.Blues

    # finish the map

    for country in shpreader.Reader(countriesShape).records():
        name = country.attributes['name_long']

        #see if key exists
        if name in countries:
            value = float(countries[name])
            ax.add_geometries(country.geometry, ccrs.PlateCarree(), facecolor=cmap(value / max, 1), label=name)
        else:
            ax.add_geometries(country.geometry, ccrs.PlateCarree(), facecolor='#FAFAFA', label=name)

    plt.title('Number of Hospitals')
    plt.savefig('%s/figure14b.png' % (options.output))

    ############
    #Figure 15 - MRI application scatter plot
    ############
    fig, ax1 = plt.subplots()
    data1 = [2500, 2900, 2400, 800, 700, 400, 400, 100]
    data2 = [25.0, 29.0, 24.0, 8.0, 7.0, 4.0, 4.0, 1.0]
    data3 = [97.0, 89.0, 99.5, 99.0, 91.0, 55.0, 19.0, 5.0]
    colors = ['b', 'b', 'b', 'y', 'y', 'r', 'r', 'r']

    labels = ['Spine', 'Brain & Head', 'Extremity', 'Vascular', 'Pelvic & Abdominal', 'Breast', 'Chest, other Cardiac', 'Other' ]
    plt.subplots_adjust(bottom = 0.1)
    plt.scatter(data2, data3, marker = 'o', c =colors, alpha=0.4, s = data1, cmap = plt.get_cmap('Spectral'))
    for label, x, y in zip(labels, data2, data3):
        if label == 'Brain & Head':
            plt.annotate(
                label,
                xy = (x, y), xytext = (60, 30),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
        elif label == 'Spine':
            plt.annotate(
                label,
                xy = (x, y), xytext = (-20, -60),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
        elif label == 'Chest, other Cardiac':
            plt.annotate(
                label,
                xy = (x, y), xytext = (60, 20),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
        else:
            plt.annotate(
                label,
                xy = (x, y), xytext = (-20, 20),
                textcoords = 'offset points', ha = 'right', va = 'bottom',
                bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))

    ax1.set_xlabel('Percent of Procedures (%)')
    ax1.set_ylabel('Percent of Sites Performing (%)')
    plt.savefig('%s/figure15.png' % (options.output))


    ############
    #Figure 16 - Closed / open MRI
    ############

    fig, ax1 = plt.subplots()
    units = [3458, 1362]
    revenues = [3638.8, 997.2]
    labels = ['Closed', 'Open']
    width = 0.35

    #axis 1 units
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, units, width, align='center', alpha=0.4, color='b', label='Units')
    ax1.set_ylabel('MRI Instruments')

    #axis 2 revenue
    ax2 = ax1.twinx()
    plot2 = ax2.bar(xPos+width, revenues, width, align='center', alpha=0.4, color='r', label='Revenue')
    ax2.set_ylabel('Revenue (Millions USD)')

    #final additions and then plot
    autolabel(plot1, ax1, units)
    autolabel(plot2, ax2, revenues)
    plt.xticks(xPos+(width/2), labels)
    plt.legend([plot1, plot2], ['Units', 'Revenue'])
    plt.savefig('%s/figure16a.png' % (options.output))

    fig, ax1 = plt.subplots()

    cagrUnits = [5.5, 10.9]
    cagrRevenues = [5.3, 9.2]

    #axis 1 units
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, cagrUnits, width, align='center', alpha=0.4, color='b', label='Units')
    ax1.set_ylabel('CAGR Units [2010 - 2018] (%)')

    #axis 2 revenue
    ax2 = ax1.twinx()
    plot2 = ax2.bar(xPos+width, cagrRevenues, width, align='center', alpha=0.4, color='r', label='Revenue')
    ax2.set_ylabel('CAGR Revenue [2010 - 2018] (%)')

    #final additions and then plot
    autolabel(plot1, ax1, cagrUnits)
    autolabel(plot2, ax2, cagrRevenues)
    plt.xticks(xPos+(width/2), labels)
    plt.legend([plot1, plot2], ['Units', 'Revenue'], loc='upper left')
    plt.savefig('%s/figure16b.png' % (options.output))

    fig, ax1 = plt.subplots()
    ax1.axis('equal')
    data = [71.7, 28.3]
    labels = ['Open MRI', 'Closed MRI']
    pie_wedge_collection = plt.pie(data, labels=labels,autopct='%1.1f%%', startangle=90)

    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor('white')

    plt.title("MRI Instruments")
    plt.savefig('%s/figure16c.png' % (options.output))

    ############
    #Figure 17 - magnet strength
    ############

    fig, ax1 = plt.subplots()
    units = [41, 887, 474]
    revenues = [10.0, 889.8, 704.7]
    labels = ['Low and Mid-Field', 'High-Field', 'Very High-Field']
    width = 0.35

    #axis 1 units
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, units, width, align='center', alpha=0.4, color='b', label='Units')
    ax1.set_ylabel('MRI Instruments')

    #axis 2 revenue
    ax2 = ax1.twinx()
    plot2 = ax2.bar(xPos+width, revenues, width, align='center', alpha=0.4, color='r', label='Revenue')
    ax2.set_ylabel('Revenue (Millions USD)')

    #final additions and then plot
    autolabel(plot1, ax1, units)
    autolabel(plot2, ax2, revenues)
    plt.xticks(xPos+(width/2), labels)
    plt.legend([plot1, plot2], ['Units', 'Revenue'], loc='upper left')
    plt.savefig('%s/figure17a.png' % (options.output))

    fig, ax1 = plt.subplots()

    cagrUnits = [1.8, 3.7, 10.0]
    cagrRevenues = [-11.2, 2.7, 8.7]

    #axis 1 units
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, cagrUnits, width, align='center', alpha=0.4, color='b', label='Units')
    ax1.set_ylabel('CAGR Units [2010 - 2018] (%)')

    #axis 2 revenue
    ax2 = ax1.twinx()
    plot2 = ax2.bar(xPos+width, cagrRevenues, width, align='center', alpha=0.4, color='r', label='Revenue')
    ax2.set_ylabel('CAGR Revenue [2010 - 2018] (%)')

    #final additions and then plot
    autolabel(plot1, ax1, cagrUnits)
    autolabel(plot2, ax2, cagrRevenues)
    plt.xticks(xPos+(width/2), labels)
    plt.legend([plot1, plot2], ['Units', 'Revenue'], loc='upper left')
    plt.savefig('%s/figure17b.png' % (options.output))

    fig, ax1 = plt.subplots()
    ax1.axis('equal')
    data = [19.01, 68.96, 12.03]
    labels = ['Low & Mid-Field', 'High-Field', 'Very High-Field']
    pie_wedge_collection = plt.pie(data, labels=labels,autopct='%1.1f%%', startangle=90)

    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor('white')

    plt.title("MRI by Magnet")
    plt.savefig('%s/figure17c.png' % (options.output))

    ############
    #Figure 18 - global instruments
    ############
    fig, ax1 = plt.subplots()
    units = [1402, 110, 670, 855, 1057, 437, 289, 4820]
    revenues = [1604.6, 109.9, 638.3, 839.8, 820.9, 392.6, 227.9, 4634.0]
    labels = ['US', 'Canada', 'Japan', 'Europe', 'APAC', 'Latin Amer', 'ROW', 'Total']
    width = 0.35

    #axis 1 units
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, units, width, align='center', alpha=0.4, color='b', label='Units')
    ax1.set_ylabel('MRI Instruments')

    #axis 2 revenue
    ax2 = ax1.twinx()
    plot2 = ax2.bar(xPos+width, revenues, width, align='center', alpha=0.4, color='r', label='Revenue')
    ax2.set_ylabel('Revenue (Millions USD)')

    #final additions and then plot
    autolabel(plot1, ax1, units)
    autolabel(plot2, ax2, revenues)
    plt.xticks(xPos+(width/2), labels)
    plt.legend([plot1, plot2], ['Units', 'Revenue'], loc='upper left')
    plt.savefig('%s/figure18a.png' % (options.output))

    fig, ax1 = plt.subplots()

    cagrUnits = [5.4, 6.7, 6.8, 5.6, 10.7, 7.3, 7.8, 7.1]
    cagrRevenues = [5.2, 6.3, 5.1, 2.5, 11.9, 7.7, 7.5, 6.2]

    #axis 1 units
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, cagrUnits, width, align='center', alpha=0.4, color='b', label='Units')
    ax1.set_ylabel('CAGR Units [2010 - 2018] (%)')

    #axis 2 revenue
    ax2 = ax1.twinx()
    plot2 = ax2.bar(xPos+width, cagrRevenues, width, align='center', alpha=0.4, color='r', label='Revenue')
    ax2.set_ylabel('CAGR Revenue [2010 - 2018] (%)')

    #final additions and then plot
    autolabel(plot1, ax1, cagrUnits)
    autolabel(plot2, ax2, cagrRevenues)
    plt.xticks(xPos+(width/2), labels)
    plt.legend([plot1, plot2], ['Units', 'Revenue'], loc='upper left')
    plt.savefig('%s/figure18b.png' % (options.output))

    fig, ax1 = plt.subplots()
    ax1.axis('equal')
    data = [29.0, 2.3, 13.9, 16.9, 24.2, 9.3, 6.3]
    labels = ['US', 'Canada', 'Japan', 'Europe', 'Asia-Pacific', 'Latin America', 'Rest of World']
    pie_wedge_collection = plt.pie(data, labels=labels,autopct='%1.1f%%', startangle=90)

    for pie_wedge in pie_wedge_collection[0]:
        pie_wedge.set_edgecolor('white')

    plt.title("MRI Market Share")
    plt.savefig('%s/figure18c.png' % (options.output))

    ############
    #Figure 19 - professional teams
    ############
    fig, ax1 = plt.subplots()
    teams = [30, 21, 30, 32, 30]
    labels = ['Baseball', 'Soccer', 'Basketball', 'Football', 'Hockey']

    #axis 1 units
    xPos = np.arange(len(labels))
    plot1 = ax1.bar(xPos, teams, align='center', alpha=0.4, color='b', label='Units')
    ax1.set_ylabel('Teams')


    #final additions and then plot
    autolabel(plot1, ax1, teams)
    plt.xticks(xPos, labels)
    plt.savefig('%s/figure19.png' % (options.output))
    '''
    ############
    #Figure 20 - conjoint result
    ############
    plt.subplots()
    features = ['Price: $250k', 'Price: $500k', 'Image: Superior', 'Magnet: High / Very-High', 'Size: Fixed', 'Form: Closed', 'Cloud: No Cloud', 'Teleradiology: No Teleradiology', 'Brand: Not Name Brand']
    data = [-4.21, -7.44, 13.76, 1.34, 0.27, -1.13, -0.98, -0.98, 0.42]

    #plot the data
    index = np.arange(len(features))
    plot = plt.barh(index, data, color='b', align='center', alpha=0.4)

    #set the individual colors now
    plot[0].set_color('b')
    plot[1].set_color('b')
    plot[2].set_color('b')
    plot[3].set_color('b')
    plot[4].set_color('r')
    plot[5].set_color('r')
    plot[6].set_color('r')
    plot[7].set_color('r')
    plot[8].set_color('r')

    xPos = np.arange(len(features))
    plt.subplots_adjust(left=0.35)
    plt.yticks(xPos, features)
    plt.xlabel('Covariate Coefficient')
    plt.title('Conjoint Analysis Result' )
    plt.savefig('%s/figure20.png' % (options.output))

    ############
    #
    ############

    ############
    #Figure X - histogram
    ############

    #fix, ax1 = plt.subplots()
    #data = [2.87 , 3.58 , 7.52 , 10.03 , 10.03 , 12.18 , 12.54 , 12.90 , 15.40 , 15.40 , 15.76 , 17.91 , 18.63 , 19.34 , 19.34 , 20.06 , 20.06 , 20.42 , 20.78 , 20.78 , 21.85 , 22.21 , 22.57 , 22.93 , 23.28 , 25.08 , 25.08 , 25.43 , 25.43 , 25.79 , 27.58 , 27.94 , 27.94 , 28.30 , 28.66 , 29.02 , 29.37 , 29.37 , 29.73 , 30.09 , 30.45 , 30.81 , 31.52 , 31.88 , 32.24 , 32.24 , 32.60 , 32.60 , 32.60 , 32.60 , 32.96 , 33.67 , 34.03 , 34.03 , 34.03 , 34.03 , 34.75 , 34.75 , 35.11 , 35.11 , 35.82 , 36.18 , 36.90 , 36.90 , 37.26 , 37.61 , 37.61 , 38.33 , 38.69 , 39.41 , 40.12 , 40.48 , 41.20 , 41.91 , 42.27 , 43.35 , 44.06 , 45.85 , 49.08 , 49.79 , 49.79 , 50.15 , 50.51 , 51.58 , 53.73 , 54.45 , 55.17 , 57.32 , 59.11 , 59.82 , 60.18 , 60.18 , 60.54 , 61.62 , 63.05 , 64.48 , 64.48 , 65.91 , 65.91 , 68.42 , 70.93 , 72.36 , 73.08 , 79.53 , 83.83 , 86.33 , 90.63 , 90.99 , 90.99 , 95.29 , 96.72 , 98.87 , 99.23 , 106.04 , 106.39 , 113.92 , 140.43 , 147.23]
    #ax1.hist(data, color='b', alpha=0.4)
    #ax1.set_xlabel('Profession Fee ($)')
    #ax1.set_ylabel('CPT Codes')
    #plt.savefig('%s/figureX.png' % (options.output))


    #plt.show()