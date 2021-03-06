#############################################################################
##  © Copyright CERN 2018. All rights not expressly granted are reserved.  ##
##                 Author: Gian.Michele.Innocenti@cern.ch                  ##
## This program is free software: you can redistribute it and/or modify it ##
##  under the terms of the GNU General Public License as published by the  ##
## Free Software Foundation, either version 3 of the License, or (at your  ##
## option) any later version. This program is distributed in the hope that ##
##  it will be useful, but WITHOUT ANY WARRANTY; without even the implied  ##
##     warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    ##
##           See the GNU General Public License for more details.          ##
##    You should have received a copy of the GNU General Public License    ##
##   along with this program. if not, see <https://www.gnu.org/licenses/>. ##
#############################################################################
"""
function for producing list of files
"""
import os
# pylint: disable=too-many-nested-blocks
def list_files_lev2(main_dir, outdir, filenameinput, filenameoutput):
    list_subdir0 = os.listdir(main_dir)

    listfilespath = list()
    listfilesflatout = list()
    for subdir0 in list_subdir0:
        subdir0full = os.path.join(main_dir, subdir0)
        if os.path.isdir(subdir0full):
            list_subdir1 = os.listdir(subdir0full)
            for subdir1 in list_subdir1:
                subdir1full = os.path.join(subdir0full, subdir1)
                if os.path.isdir(subdir1full):
                    list_files_ = os.listdir(subdir1full)
                    for myfile in list_files_:
                        filefull = os.path.join(subdir1full, myfile)
                        if os.path.isfile(filefull) and \
                        myfile == filenameinput:
                            listfilespath.append(filefull)
                            filefullflat = filefull.replace("/", "_")
                            filefullflat = filefullflat.replace(filenameinput, filenameoutput)
                            filefullflat = outdir + filefullflat
                            listfilesflatout.append(filefullflat)
    return listfilespath, listfilesflatout

# pylint: disable=too-many-nested-blocks
def list_files_dir_lev2(main_dir, outdir, filenameinput, filenameoutput):
    list_subdir0 = os.listdir(main_dir)

    listfilespath = list()
    listfilesflatout = list()
    for subdir0 in list_subdir0:
        subdir0full = os.path.join(main_dir, subdir0)
        outdir0full = os.path.join(outdir, subdir0)
        if not os.path.exists(outdir0full) and os.path.isdir(subdir0full):
            os.makedirs(outdir0full)
        if os.path.isdir(subdir0full):
            list_subdir1 = os.listdir(subdir0full)
            for subdir1 in list_subdir1:
                subdir1full = os.path.join(subdir0full, subdir1)
                outdir1full = os.path.join(outdir0full, subdir1)
                if not os.path.exists(outdir1full) and os.path.isdir(subdir1full):
                    os.makedirs(outdir1full)
                if os.path.isdir(subdir1full):
                    list_files_ = os.listdir(subdir1full)
                    for myfile in list_files_:
                        filefull = os.path.join(subdir1full, myfile)
                        filefullout = os.path.join(outdir1full, myfile)
                        filefullout = filefullout.replace(filenameinput, \
                                                          filenameoutput)
                        if os.path.isfile(filefull) and \
                        myfile == filenameinput:
                            listfilespath.append(filefull)
                            listfilesflatout.append(filefullout)
    return listfilespath, listfilesflatout

def create_subdir_list_lev1(outdir, length, filename):
    listfilespath = list()
    mergeddir = os.path.join(outdir, "merged")
    if not os.path.exists(mergeddir):
        os.makedirs(mergeddir)
    for index in range(1, length+1):
        subdir = "%d"  % index
        subdirfull = os.path.join(mergeddir, subdir)
        if not os.path.exists(subdirfull):
            os.makedirs(subdirfull)
        filefull = os.path.join(subdirfull, filename)
        listfilespath.append(filefull)
    return listfilespath

def read_subdir_list_lev1(main_dir, filename, filenameout):
    merged_dir = os.path.join(main_dir, "merged")
    list_subdir0 = os.listdir(merged_dir)
    listfilespath = list()
    listfilespathout = list()
    print(list_subdir0)
    for subdir0 in list_subdir0:
        subdir0full = os.path.join(merged_dir, subdir0)
        filefull = os.path.join(subdir0full, filename)
        filefullout = filefull.replace(filename, filenameout)
        if os.path.exists(filefull):
            listfilespath.append(filefull)
            listfilespathout.append(filefullout)
    return listfilespath, listfilespathout


# pylint: disable=too-many-nested-blocks
def list_files_dir_lev1(main_dir, outdir, filenameinput, filenameoutput):
    list_subdir0 = os.listdir(main_dir)

    listfilespath = list()
    listfilesflatout = list()
    for subdir0 in list_subdir0:
        subdir0full = os.path.join(main_dir, subdir0)
        outdir0full = os.path.join(outdir, subdir0)
        if not os.path.exists(outdir0full) and os.path.isdir(subdir0full):
            os.makedirs(outdir0full)
        if os.path.isdir(subdir0full):
            list_files_ = os.listdir(subdir0full)
            for myfile in list_files_:
                filefull = os.path.join(subdir0full, myfile)
                filefullout = os.path.join(outdir0full, myfile)
                filefullout = filefullout.replace(filenameinput, filenameoutput)
                if os.path.isfile(filefull) and \
                    myfile == filenameinput:
                    listfilespath.append(filefull)
                    listfilesflatout.append(filefullout)
    return listfilespath, listfilesflatout

def list_files_lev1(main_dir, outdir, filenameinput, filenameoutput):
    list_subdir0 = os.listdir(main_dir)

    listfilespath = list()
    listfilesflatout = list()
    for subdir0 in list_subdir0:
        subdir0full = os.path.join(main_dir, subdir0)
        if os.path.isdir(subdir0full):
            list_files_ = os.listdir(subdir0full)
            for myfile in list_files_:
                filefull = os.path.join(subdir0full, myfile)
                if os.path.isfile(filefull) and myfile == filenameinput:
                    listfilespath.append(filefull)
                    filefullflat = filefull.replace("/", "_")
                    filefullflat = filefullflat.replace(filenameinput, filenameoutput)
                    filefullflat = outdir + filefullflat
                    listfilesflatout.append(filefullflat)
    return listfilespath, listfilesflatout
