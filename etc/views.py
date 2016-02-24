from django.http import HttpResponse
from django.shortcuts import render
from django.template import Context

from django.template.loader import get_template

from .forms import AtmosphericConditionsForm, ObservationalSetupForm
from .forms import TargetForm, InstrumentForm
from .models import PhotometricFilter
from .models import SpectralTemplate, VPHSetup

from justcalc import calc
from plot1 import plot_and_save, plot_and_save2, plot_and_save_new, plot_and_save2_new

import numpy
import os
import tempfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import mpld3

#/home/pica/Documents/virt_django/django_megara


def compute5(request):
    print request.POST['stype']
    size_val = 1.0 if request.POST['stype']== 'P' else request.POST['size']
    mag_val = float(request.POST['contmagval']) if request.POST['contmagflux'] == 'M' else 20.0
    fc_val = 1e-16 if request.POST['contmagflux'] == 'M' else float(request.POST['contfluxval'])


    fluxt_val = request.POST['iflux']
    if fluxt_val == "C":
        resolvedline_val = "N"
        fline_val = 1e-13
        wline_val = 6562.8
        fwhmline_val = 6
        nfwhmline_val = 1.0
        cnfwhmline_val = 1.0

    else:
        fline_val = float(request.POST['lineflux'])
        wline_val = float(request.POST['linewave'])
        nfwhmline_val = float(request.POST['lineap'])
        cnfwhmline_val = float(request.POST['contap'])
        if fluxt_val == "L" and request.POST['rline'] == "N":
            resolvedline_val = "N"
            fwhmline_val = 6

        elif fluxt_val == "L" and request.POST['rline'] == "Y":
            resolvedline_val = "Y"
            fwhmline_val = float(request.POST['linefwhm'])


    querybandc = PhotometricFilter.objects.filter(pk=request.POST['pfilter']).values()  # get row with the values at primary key
    bandc_val = querybandc[0]['name']
    # entry_filter_cwl = querybandc[0]['cwl']
    # entry_filter_width = querybandc[0]['path']

    queryvph = VPHSetup.objects.filter(pk=request.POST['vph']).values()
    vph_val = queryvph[0]['name']

    if vph_val == '-empty-':        # Deals with -empty- VPH Setup
        # vph_val = 'MR-UB'
        outtext="WARNING: VPH Setup is -empty-! Choose a VPH."
        texti=" "
        textoc=" "
        textol=" "
        outputfilename="etc/static/etc/outputcalc.txt"
        with open(outputfilename, 'w') as f:
            print >> f, outtext
            print >> f, texti
            print >> f, textoc
            print >> f, textol
        outputofcalc = ({'outtext':outtext, 'texti':texti, 'textoc':textoc, 'textol':textol})
        # return outputofcalc
    else:
        entry_vph_fwhm = queryvph[0]['fwhm']
        entry_vph_disp = queryvph[0]['dispersion']
        entry_vph_deltab = queryvph[0]['deltab']
        entry_vph_lambdac = queryvph[0]['lambdac']
        entry_vph_relatedband = queryvph[0]['relatedband']
        entry_vph_lambdab = queryvph[0]['lambda_b']
        entry_vph_lambdae = queryvph[0]['lambda_e']
        entry_vph_specconf = queryvph[0]['specconf']

        # vphfeatures = [entry_vph_fwhm,entry_vph_disp,entry_vph_deltab,entry_vph_lambdac,\
        #                entry_vph_relatedband,entry_vph_lambdab,entry_vph_lambdae,entry_vph_specconf]
        # filtercar2 = ["0","0",entry_vph_lambdab,entry_vph_lambdae]

        spec = request.POST['spectype']
        queryspec = SpectralTemplate.objects.filter(pk=spec).values()
        entry_spec_name = queryspec[0]['name']
        # entry_spec_path = queryspec[0]['path']
        # spectdat = [entry_spec_name,entry_spec_path]
        spect_val = entry_spec_name

        moon_val = request.POST['moonph']
        airmass_val = float(request.POST['airmass'])
        seeing_val = float(request.POST['seeing'])
        numframes_val = float(request.POST['numframes'])
        exptimepframe_val = float(request.POST['exptimepframe'])
        nsbundles_val = int(request.POST['nfibers'])

        outputofcalc = calc(request.POST['stype'],request.POST['contmagflux'],mag_val,fc_val,size_val,fluxt_val,\
                            fline_val,wline_val,nfwhmline_val,cnfwhmline_val,
                            fwhmline_val,resolvedline_val,spect_val,bandc_val,\
                            request.POST['om_val'],vph_val,moon_val,airmass_val,seeing_val,\
                            numframes_val,exptimepframe_val,nsbundles_val)


    # cleanstring = string1.replace("\'", '\n')
    # cleanstring = cleanstring.replace(",", ' ')
    # cleanstring = cleanstring.replace("u\n", '\n')
    # cleanstring = cleanstring[1:].replace("(", '\n')
    # cleanstring = cleanstring[:-1].replace("(", '\n')

    # cleanstring = [outtextstring,inputstring,coutputstring,loutputstring]

    return outputofcalc

##############################################################################################################################
##############################################################################################################################
def basic(request):
    return render(request, 'etc/index.html')

def get_info(request):
    # if this is a POST request we need to process the form data
    if request.method == 'GET':
        # create a form instance and populate it with data from the request:
        form1 = TargetForm(request.GET)
        form2 = InstrumentForm(request.GET)
        form3 = AtmosphericConditionsForm(request.GET)
        form4 = ObservationalSetupForm(request.GET)

    # if a GET (or any other method) we'll create a blank form
    else:
        form1 = TargetForm()
        form2 = InstrumentForm()
        form3 = AtmosphericConditionsForm()
        form4 = ObservationalSetupForm()

    return render(request, 'etc/webmegaraetc-0.4.2.html', {
                                             'form1': form1,
                                             'form2': form2,
                                             'form3': form3,
                                             'form4': form4,
                                             })



# LOADS THIS AFTER PUSHING "START" in index.html
def etc_form(request):
    form1 = TargetForm()
    form2 = InstrumentForm()
    form3 = AtmosphericConditionsForm()
    form4 = ObservationalSetupForm()

    total_formu = {'form1': form1,
                   'form2': form2,
                   'form3': form3,
                   'form4': form4,
                   }

    return render(request, 'etc/webmegaraetc-0.4.2.html', total_formu)


# LOADS THIS AFTER PRESSING "COMPUTE" webmegaraetc.html and
# OUTPUT RESULTS in result.html
# FINAL STRING CLEANSING/FILTERING HERE
#
#
def etc_do(request):
    if request.method == 'GET':
        # import matplotlib.pyplot as plt
        # import mpld3
        # from mpld3 import plugins, utils
        #
        # plt.plot([3,1,4,1,5], 'ks-', mec='w', mew=5, ms=20)
        # mpld3.save_html()
        return HttpResponse("<html><body>It works!</body></html>")

    elif request.method == 'POST':
        outputofcalc = compute5(request)

        tocheck = str(outputofcalc['outtext'])
        if not tocheck:
            outtextstring = ""  #No warning.
        else:
            outtextstring = tocheck

        # GET relevant data
        vph = request.POST['vph']
        queryvph = VPHSetup.objects.filter(pk=vph).values()
        vph_val = queryvph[0]['name']
        spec = request.POST['spectype']
        queryspec = SpectralTemplate.objects.filter(pk=spec).values()
        entry_spec_name = queryspec[0]['name']

        if not tocheck:
            x = outputofcalc['lamb']
            y = outputofcalc['fc']
            label1 = entry_spec_name
            label2 = outputofcalc['mag_val']
            label3 = outputofcalc['bandc_val']

            x2 = outputofcalc['lamb']
            y2 = outputofcalc['pframesn_psp_asp']
            x2b = x2
            y2b = outputofcalc['allframesn_psp_asp']
            x2c = x2
            y2c = outputofcalc['pframesn_psp_asp_all']
            x2d = x2
            y2d = outputofcalc['allframesn_psp_asp_all']


            label2a = entry_spec_name
            label2b = vph_val
            label2c = outputofcalc['bandc_val']
        else:
            x = numpy.arange(1, 100, 1)
            y = numpy.arange(1, 100, 1)
            x2 = numpy.arange(1, 100, 1)
            y2 = numpy.arange(1, 100, 1)
            x2b = numpy.arange(1, 100, 1)
            y2b = numpy.arange(1, 100, 1)
            x2c = numpy.arange(1, 100, 1)
            y2c = numpy.arange(1, 100, 1)
            x2d = numpy.arange(1, 100, 1)
            y2d = numpy.arange(1, 100, 1)



            label1 = "none"
            label2 = 20.0   # Float
            label3 = "none"
            label2a = "none"
            label2b = "none"
            label2c = "none"

        # # CREATE TEMPORARY FILE
        # temp = tempfile.NamedTemporaryFile(suffix=".png", prefix="temp", dir="etc/static/etc/tmp/", delete=False)
        #
        # graphic = plot_and_save(temp.name, x, y, label1, label2, label3)
        # temp2 = tempfile.NamedTemporaryFile(suffix=".png", prefix="temp", dir="etc/static/etc/tmp/", delete=False)
        # graphic2 = plot_and_save2(temp2.name, x2, y2, x2b, y2b, x2c, y2c, x2d, y2d, label2a, label2b, label2c)
        #
        # # RENAME FILE PATH
        # dirname, basename = os.path.split(graphic)
        # newpath = '/static/etc/tmp/'
        # graphic = os.path.join(newpath, basename)
        #
        # dirname2, basename2 = os.path.split(graphic2)
        # newpath2 = '/static/etc/tmp/'
        # graphic2 = os.path.join(newpath2, basename2)

        inputstring = '<br /><p>' + str(outputofcalc['texti']) + '</p>'
        coutputstring = '<br /><p>' + str(outputofcalc['textoc']) + '</p>'
        loutputstring = '<br /><p>' + str(outputofcalc['textol']) + '</p>'

        figura = plot_and_save_new('', x, y, label1, label2, label3)
        html = mpld3.fig_to_html(figura)
        figura2 = plot_and_save2_new('', x2, y2, x2b, y2b, x2c, y2c, x2d, y2d, label2a, label2b, label2c)
        html += mpld3.fig_to_html(figura2)

        html = html.replace("None", "")  # No se xq introduce string None

        from django.http import JsonResponse
        return JsonResponse({'outtext' : outtextstring,
                             'textinput' : inputstring,
                             'textcout' : coutputstring,
                             'textlout' : loutputstring,
                             'graphic' : html,
                             })


def etc_tab(request):
    if request.method == 'GET':
        outputofcalc = compute5(request)

        tocheck = str(outputofcalc['outtext'])
        if not tocheck:
            outtextstring = "No warning."
        else:
            outtextstring = tocheck
        inputstring = str(outputofcalc['texti'])
        coutputstring = str(outputofcalc['textoc'])
        loutputstring = str(outputofcalc['textol'])

        return render(request, 'etc/tab.html',
            context={
                      'outtext':outtextstring,
                      'textinput':inputstring,
                      'textcout':coutputstring,
                      'textlout':loutputstring
                     }
                      )
