"""
-----------------------------------------------------------------------------
This source file is part of OSTIS (Open Semantic Technology for Intelligent Systems)
For the latest info, see http://www.ostis.net

Copyright (c) 2011 OSTIS

OSTIS is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OSTIS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OSTIS.  If not, see <http://www.gnu.org/licenses/>.
-----------------------------------------------------------------------------
"""

'''
Created on 13.10.10

@author: DenisKoronchik
@modified: Dmitry Kolb
'''
import os, sys, traceback
from pyparsing import *

script_dir = os.path.abspath(os.curdir)#os.path.dirname(os.path.abspath(__file__))
#sys.path.append(os.path.join(script_dir, "repoBuilder"))

import shutil
import re
import repoBuilder.scg_build as scg_build
import repoBuilder.defines as defines
import xml.dom.minidom as xml

type = oneOf("scg inc scn scs new gwfkey")
par = oneOf("beg end")
direction = oneOf("-> <-")
arg = QuotedString('"',endQuoteChar='"')
comment = pythonStyleComment
rule = Group(type + Suppress(Literal(":>")) + Optional(par) + arg + Optional(direction) + Optional(arg) + Optional(arg) + Optional(arg) + Optional(arg))
rules  = OneOrMore(rule^Suppress(comment))

self = sys.modules[globals()['__name__']]


def apply_rule(rule):
    
    print "Aplying rule '%s'..." % rule
    
    #m = re.match(r'(.*)\:\> (.*)', rule)
    
    if not rule:
        print "Error to apply rule '%s'" % rule
        return
    
    rule_type = rule[0]
    rule_value = rule[1:] 
    
    # get rule applier
    try:
        func = getattr(self, "apply_rule_%s" % rule_type)
    except:
        print "Unknown rule type '%s'" % rule_type
        print "Error:", sys.exc_info()[0]
        traceback.print_exc(file=sys.stdout)

    func(rule_value)
        
def apply_rule_scg(rule):
    
    # get source directory and output segment
    
    src_dir = rule[0]
    seg = rule[2]
    
    # apply rule
    try:
        scg_build.generate_scg(os.path.join(defines.PATH_REPO_SRC, seg + ".scg"),
                                os.path.join(defines.PATH_REPO_SRC, src_dir))
    except:
        print "Error during apply scg rule '%s'" % rule
        print "Error:", sys.exc_info()[0]
        traceback.print_exc(file=sys.stdout)
		
def apply_rule_scs(rule):
	
	seg = os.path.join(defines.PATH_REPO_SRC, rule[2] + ".scs")
	src_dir = os.path.join(defines.PATH_REPO_SRC, rule[0])
	
	print "Generating scs file '%s' from '%s'" % (seg, src_dir)
	
	#  make includes as params
	includes = ["ordinal.scsy", "meta_info.scsy", "ui_keynodes.scsy", "com_keynodes.scsy", "_keynodes.scsy"]

	out_file = open(seg, "w")
	for inc in includes:
		out_file.write('#include "%s"\n' % inc)	

	
	for root, dirs, files in os.walk(src_dir):

		print "scanning %s" % (os.path.join(root))
		
		for file in files:
			if file.endswith(".scsy"):
				#print seg + " -> " +root
				fin = os.path.join(os.path.relpath(root, os.path.dirname(seg)), file)				
				print "adding file %s" % (fin)
				out_file.write('#include "%s"\n' % fin)
			else:
				print "ignored %s in %s" % (file, src_dir)

	out_file.write('\n')
	out_file.close()

        
def apply_rule_inc(rule):

    # get source file and includes
    #m = re.match(r'(beg|end) \"(.*)\" \<\- \"(.*)\"', rule)
    
    pos = rule[0]
    source = rule[1]
    inc = rule[3]
    
    source = os.path.join(defines.PATH_REPO_SRC, source)
    
    try:
        data = open(source, "r").read()
        if pos == "beg":
            data = ('#include "%s"\n' % inc) + data
        elif pos == "end":
            data = data + ('\n\n#include "%s"' % inc)
        open(source, "w").write(data)
    except:
        print "Error during apply inc rule '%s'" % rule
        print "Error:", sys.exc_info()[0]
        traceback.print_exc(file=sys.stdout)
		
def apply_rule_scn(rule):
    #sys.path.append("repoBuilder")
    import repoBuilder.SCnML2SC.SCnML2SC as SCnML2SC
    output = os.path.join(defines.PATH_REPO_SRC, rule[2])
    if os.path.isdir(output):
        shutil.rmtree(output)
    os.mkdir(output)
    
    SCnML2SC.download(kb_seg = rule[0],
                    scn_seg = rule[1],
                    _wikiUrl = rule[3],
                    _category = rule[4],
                    outDir = os.path.join(defines.PATH_REPO_SRC, rule[2]))
                    
def apply_rule_new(rule):
    
    output = os.path.join(defines.PATH_REPO_SRC, rule[0])
    fl = open(output, "w")
    fl.write("//# File generated by rule_builder\n")
    fl.close()
    
def apply_rule_gwfkey(rule):
    
    segment = rule[3]
    if segment[-1] == "/":
        segment = segment[:-1]
    doc = xml.parse(os.path.join(defines.PATH_REPO_SRC, rule[0]))
    
    fl = open(os.path.join(defines.PATH_REPO_SRC, rule[2]), "a+")
    fl.write("\n\n//# %s\n" % rule[0])
    gwf_node = doc.childNodes[0]
    
    node_tags = gwf_node.getElementsByTagName("node")
    for tag in node_tags:
        idtf = tag.attributes["idtf"].value
        if len(idtf) == 0:
            continue
           
        fl.write('"%s"\t=\t"%s/%s";\n' % (idtf, segment, idtf))
        
    fl.close()

    
def build(rules_file):
    # read file with rules
    #rules = open(os.path.join(script_dir, rules_file), "r").readlines()
    global rules
    tokens = rules.parseFile(os.path.join(script_dir, rules_file))

    
    print "#" * 25
    print "# aply rules from file '%s'" % rules_file
    print "#" * 25
    
    for tok in tokens:
        apply_rule(tok)
    
    # building scg files with base sources
    #print "Adding gwf files to test segment"
    #print defines.PATH_REPO_SRC
    #scg_build.generate_scg(os.path.join(defines.PATH_REPO_SRC, test_seg_uri + ".scg"),
    #                                    os.path.join(defines.PATH_REPO_SRC, test_gwf_dir))
    
    # building repository
#    print "#" * 25
#    print "# Building repository"
#    print "#" * 25
    from repoBuilder.builder import Builder
    builder = Builder()
    builder.run()
    
if __name__ == '__main__':
    #os.chdir("repoBuilder")
   
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--bin", dest = "bin",
                      help = "use specified binary path",
                      metavar = "BIN", default = 'repoBuilder')
    parser.add_option("--fs_repo_src", dest = "fs_repo_src",
                      help = "use specified path for fs_repo_src",
                      metavar = "FS_REPO_SRC", default = '../fs_repo_src')
    parser.add_option("--fs_repo", dest = "fs_repo",
                      help = "use specified path for fs_repo",
                      metavar = "FS_REPO", default = '../fs_repo')                       
    (options, args) = parser.parse_args()
    
    defines.PATH_REPO_SRC = options.fs_repo_src
    defines.PATH_REPO_BIN = options.fs_repo
    defines.INCLUDES = os.path.join(defines.PATH_REPO_SRC, "include")
    
    os.chdir(options.bin)
    rules_file = "build.rules"
    build(rules_file)