#! /usr/bin/env python
#===================================================================================
# FILE: MendeleyUpdate.py
#
# USAGE: ./MendeleyUpdate.py [FILE]
#
# DESCRIPTION: Updates Menedley Database.
# Checks for all entries that have an arXiv ID but not a DOI.
# Queries the SAO/NASA Astrophysics Data System to check for assigned DOI.
# If DOI is available, updates sqlite database and moves entry to 'Needs Review'.
# To update full article information, use Mendeley for DOI lookup.
#
# OPTIONS: ---
# REQUIREMENTS: ---
# BUGS: ---
# NOTES: ---
# AUTHOR: Michael Lund, Mike.Lund@gmail.com
# COMPANY: ---
# VERSION: 1.0
# CREATED: 23.05.2015 - 20:52:00
# REVISION: ---
#===================================================================================

import re
import urllib
import sqlite3
import sys
__version__ = '1.0'

def usage():
   print u"Useage: MendeleyUpdate.py FILE\n"
   print u"Options\n-h, --help\tHelp\n-v\t\tVerbose mode; displays every line being queried"
   print "\nDescription:\nUpdates Menedley Database.\nChecks for all entries that have an arXiv ID but not a DOI.\nQueries the SAO/NASA Astrophysics Data System to check for assigned DOI.\nIf DOI is available, updates sqlite database and moves entry to 'Needs Review'.\nTo update full article information, use Mendeley for DOI lookup.\n"
   print "Mendeley sqlite database named <<yourEmailAddress>>@www.mendeley.com.sqlite, or online.sqlite if no email address used with Mendeley."
   print "Mendeley Desktop database file locations:\nWindows Vista/Windows 7: %LOCALAPPDATA%\Mendeley Ltd.\Mendeley Desktop\\\nWindows XP: C:\Documents and Settings\<<Your Name>>\Local Settings\Application Data\Mendeley Ltd\Mendeley Desktop\\\nLinux: ~/.local/share/data/Mendeley Ltd./Mendeley Desktop/\nMacOS: Macintosh HD -> /Users/<<Your Name>>/Library/Application Support/Mendeley Desktop/"

# take arXivID and add to web address for ADS query; returns DOI or NA if no DOI listed
def get_DOI(arxivID):
   if re.match('ArXiv:', arxivID):
      webpage="http://adsabs.harvard.edu/cgi-bin/bib_query?"+arxivID
   else:
      webpage="http://adsabs.harvard.edu/cgi-bin/bib_query?ArXiv:"+arxivID
   try: sock=urllib.urlopen(webpage)
   except: print "Unable to reach ADS website"; sys.exit()
   htmlSource=sock.read()
   sock.close()
   temp=re.sub('<.*?>','',htmlSource)
   answer='NA'
   for item in temp.split("\n"):
      if "DOI:" in item:
         answer=item.strip()
   return answer.split(':')[-1]

if __name__ == "__main__":
   verbose=False
   if ('-h' in sys.argv) or ('--help' in sys.argv): usage(); sys.exit()
   if '-v' in sys.argv:
      verbose=True
      sys.argv.remove('-v')
   try:
      sqlite_file = sys.argv[1]
   except:
      usage()
      sys.exit()
   #sets variables to the sqlite table and columns used by Mendeley
   table_name= 'Documents'
   id_column = 'id'
   arxiv_column = 'arxivId'
   DOI_column = 'doi'
   confirm_column = 'confirmed'


   # Connecting to the database file
   conn = sqlite3.connect(sqlite_file, isolation_level=None)
   c = conn.cursor()
   #retrieve database ID, DOI, arXivID for all rows with an arXivID but no DOI
   c.execute('SELECT {cid}, {coi1},{coi2} FROM {tn} WHERE {coi1} IS NULL AND {coi2} IS NOT NULL'.\
           format(cid=id_column, coi1=DOI_column, coi2=arxiv_column, tn=table_name))
   all_rows = c.fetchall()
   if verbose: print '%5s %7s %16s \t%s' % ('sqlID', 'OldDOI', 'arXivID', 'NewDOI')
   counter=0
   for row in all_rows:
      idnumber=row[0]
      temp=re.sub('v.$','',row[2])
      DOInumber=get_DOI(temp)
      if verbose: print '%5s %7s %16s \t%s' % (idnumber, row[1], temp, DOInumber)
      #update SQLite file with new DOI; mark as not confirmed
      if DOInumber is not 'NA':
         c.execute('UPDATE {tn} SET confirmed=?, {coi1}=? WHERE {cid}=?'.\
           format(cid=id_column, coi1=DOI_column, coi2=arxiv_column, tn=table_name), ('false', DOInumber, idnumber))
         counter+=1
   print counter," documents updated"

   conn.commit()
   c.close()
   conn.close()

