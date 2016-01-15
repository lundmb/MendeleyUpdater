#!/usr/bin/env python
import argparse
import ads
import sqlite3
import re
import sys
import os.path
def dev_key_check():
   if os.path.isfile(os.path.expanduser('~/.ads/dev_key')):
      print "Dev key file exists"
   else:
      print "Need file"

# take arXivID and add to web address for ADS query; returns DOI or NA if no DOI listed
def get_DOI(arxivID):
   import urllib
   if re.match('ArXiv:', arxivID):
      webpage="http://adsabs.harvard.edu/cgi-bin/bib_query?"+arxivID
   elif re.match('arXiv:', arxivID):
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

def nonAPI():
   table_name= 'Documents'
   id_column = 'id'
   arxiv_column = 'arxivId'
   DOI_column = 'doi'
   confirm_column = 'confirmed'
   abstract_column = 'abstract'
   publication_column = 'publication'
   year_column = 'year'
   issue_column = 'issue'
   volume_column = 'volume'
   sqlite_file = args.Mendeley_db
   
   # Connecting to the database file
   conn = sqlite3.connect(sqlite_file, isolation_level=None)
   c = conn.cursor()
   #retrieve database ID, DOI, arXivID for all rows with an arXivID but no DOI
   c.execute('SELECT {cid}, {coi1},{coi2} FROM {tn} WHERE {coi1} IS NULL AND {coi2} IS NOT NULL'.\
           format(cid=id_column, coi1=DOI_column, coi2=arxiv_column, tn=table_name))
   all_rows = c.fetchall()
   if args.verbose: print '%5s %7s %16s \t%s' % ('sqlID', 'OldDOI', 'arXivID', 'NewDOI')
   counter=0
   for row in all_rows:
      idnumber=row[0]
      temp=re.sub('v.$','',row[2])
      DOInumber=get_DOI(temp)
      if args.verbose: print '%5s %7s %16s \t%s' % (idnumber, row[1], temp, DOInumber)
      #update SQLite file with new DOI; mark as not confirmed
      if DOInumber is not 'NA':
         c.execute('UPDATE {tn} SET confirmed=?, {coi1}=? WHERE {cid}=?'.\
           format(cid=id_column, coi1=DOI_column, coi2=arxiv_column, tn=table_name), ('false', DOInumber, idnumber))
         counter+=1
   print counter," documents updated"

   conn.commit()
   c.close()
   conn.close()

def get_paper_info(doi_val, arXiv_val):
   #print doi_val, arXiv_val
   if arXiv_val: arXiv_val=re.sub('v.$','',arXiv_val)
   if doi_val:
      if doi_val.startswith('10.'): papers= list(ads.SearchQuery(doi=doi_val))
   elif arXiv_val: papers= list(ads.SearchQuery(arXiv=arXiv_val))
   else: print "No DOI or ArXiv ID."; return None
   if len(papers) < 1: print"No valid paper found!"; return None
   elif len(papers) > 1: print "Multiple matching papers!"; return None
   else: return papers[0]

def ADS_API():
   table_name= 'Documents'
   keyword_table = 'DocumentKeywords'
   id_column = 'id'
   arxiv_column = 'arxivId'
   DOI_column = 'doi'
   confirm_column = 'confirmed'
   abstract_column = 'abstract'
   publication_column = 'publication'
   year_column = 'year'
   issue_column = 'issue'
   volume_column = 'volume'
   page_column = 'pages'
   sqlite_file = args.Mendeley_db
   
   conn = sqlite3.connect(sqlite_file, isolation_level=None)
   c = conn.cursor()
   c.execute('SELECT {cid}, {coi1}, {coi2}, {coi3}, {coi4}, {coi5}, {coi6}, {coi7}, {coi8} FROM {tn} WHERE {coi2} IS NOT NULL OR {coi1} IS NOT NULL'.\
           format(cid=id_column, coi1=DOI_column, coi2=arxiv_column, coi3=abstract_column, coi4=publication_column, coi5=year_column, coi6=issue_column, coi7=volume_column, coi8=page_column, tn=table_name))
   all_rows = c.fetchall()
   counter0, counter1, counter2, counter3, counter4, counter5 =0,0,0,0,0,0
   for row in all_rows:
      article_updated=0
      Doc_ID=row[0]
      #print Doc_ID
      if Doc_ID <= args.start: continue
      fetch=False
      if (args.DOI and row[1]==None ): fetch=True
      if (args.abstract and row[3]==None ): fetch=True
      if (args.pub and (row[4]==None or row[5]==None or row[6]==None or row[7]==None )): fetch=True
      if args.keyword: fetch=True
      if fetch==False: continue
      # query ADS
      try: paper_info=get_paper_info(row[1], row[2])
      except Exception as e : print "ADS API error:", e; break
      if not paper_info: print "Can't find paper!", row[1], row[2], "\n"; continue
      if args.verbose: print paper_info
      DOInumber=None
      arXivnumber=None
      for identifier in paper_info.identifier:
         if identifier.startswith('10.'): DOInumber=identifier
         if identifier.startswith('arXiv:'): arXivnumber=identifier
      abstract_text=paper_info.abstract
      # add DOI
      if (args.DOI and row[1]==None and DOInumber!=None):
         c.execute('UPDATE {tn} SET {coi1}=? WHERE {cid}=?'.\
            format(cid=id_column, coi1=DOI_column, tn=table_name), (DOInumber, row[0]))
         counter1=counter1+1; article_updated=1
         if args.verbose:
            print "Added DOI:", DOInumber, "for",row[2]
         if args.verify:
            c.execute('UPDATE {tn} SET confirmed=?, WHERE {cid}=?'.\
               format(cid=id_column, tn=table_name), ('false', row[0]))
      # add arXiv
      if (args.arXiv and row[2]==None and arXivnumber!=None):
         c.execute('UPDATE {tn} SET {coi1}=? WHERE {cid}=?'.\
            format(cid=id_column, coi1=arxiv_column, tn=table_name), (arXivnumber, row[0]))
         counter2=counter2+1; article_updated=1
         if args.verbose:
            print "Added arXiv ID:", arXivnumber, "for",row[1]
         if args.verify:
            c.execute('UPDATE {tn} SET confirmed=?, WHERE {cid}=?'.\
               format(cid=id_column, tn=table_name), ('false', row[0]))
      # add abstract info
      if (args.abstract and row[3]==None and abstract_text!=None):
         c.execute('UPDATE {tn} SET {coi3}=? WHERE {cid}=?'.\
            format(cid=id_column, coi3=abstract_column, tn=table_name), (abstract_text, row[0]))
         counter3=counter3+1; article_updated=1
         if args.verbose:
            if row[2]: print "Added abstract for", row[2]
            else: print "Added abstract for", row[1]
         if args.verify:
            c.execute('UPDATE {tn} SET confirmed=?, WHERE {cid}=?'.\
               format(cid=id_column, tn=table_name), ('false', row[0]))
      # add publication info
      year_val=paper_info.year
      volume_val=paper_info.volume
      pub_val=paper_info.pub
      issue_val=paper_info.issue
      page_val=paper_info.page[0]
      if (args.pub and ((row[4]==None and pub_val) or (row[5]==None and year_val) or (row[6]==None and issue_val) or (row[7]==None and volume_val) or (row[8]==None and page_val))):
         if pub_val.lower():
            if 'arxiv' in pub_val.lower(): print ""; continue
         if args.verbose:
            print "Adding publication info:", year_val, pub_val, volume_val, issue_val, page_val
         c.execute('UPDATE {tn} SET {coi4}=?, {coi5}=?, {coi6}=?, {coi7}=?, {coi8}=? WHERE {cid}=?'.\
            format(cid=id_column, coi4=publication_column, coi5=year_column, coi6=issue_column, coi7=volume_column, coi8=page_column, tn=table_name), (pub_val, year_val, issue_val, volume_val, page_val, row[0]))
         counter4=counter4+1; article_updated=1
         if args.verify:
            c.execute('UPDATE {tn} SET confirmed=?, WHERE {cid}=?'.\
               format(cid=id_column, tn=table_name), ('false', row[0]))
      # add keywords
      if args.keyword:
            #print row[0]
            c.execute('SELECT keyword FROM {tn} WHERE documentId=?'.\
               format(tn=keyword_table), (Doc_ID,))
            keyword_list = c.fetchall()
            keyword_list=[x[0] for x in keyword_list]
            if keyword_list==None: keyword_list=[]
            if paper_info.keyword==None: paper_info.keyword=[]
            new_keywords=list(set(paper_info.keyword) - set(keyword_list))
            if new_keywords==None or new_keywords==[]:
               if args.verbose: print "No new keywords"
            else:
               print "Adding new keywords:", new_keywords               
               for keyword_item in new_keywords:
                  c.execute('INSERT INTO {tn} ({col1}, {col2}) VALUES (?,?)'.\
                     format(tn=keyword_table, col1='documentId', col2='keyword'), (Doc_ID, keyword_item))
               counter5=counter5+1; article_updated=1
      
      if args.verbose: print ""
      counter0=counter0+article_updated
      #if counter0>20: break
   #print len(all_rows)
   #conn.commit()
   c.close()
   conn.close()
   print "DOI number added for", counter1, "entries"
   print "ArXiv number added for", counter2, "entries"
   print "Abstracts added for", counter3, "entries"
   print "Publication info added for", counter4, "entries"
   print "Author keywords added for", counter5, "entries"
   print counter0, "total updated entries, of", Doc_ID-args.start-1, "entries checked!"
   print len(all_rows), "entries total"



if __name__ == "__main__":
   dev_key_check()
   description_text="Mendeley sqlite database named <<yourEmailAddress>>@www.mendeley.com.sqlite, or online.sqlite if no email address used with Mendeley. Mendeley Desktop database file locations: ||Windows Vista/Windows 7: %LOCALAPPDATA%\Mendeley Ltd.\Mendeley Desktop ||Windows XP: C:\Documents and Settings\<<Your Name>>\Local Settings\Application Data\Mendeley Ltd\Mendeley Desktop ||Linux: ~/.local/share/data/Mendeley Ltd./Mendeley Desktop/ ||MacOS: Macintosh HD -> /Users/<<Your Name>>/Library/Application Support/Mendeley Desktop/"
   parser = argparse.ArgumentParser(description=description_text)
   parser.add_argument("Mendeley_db", type=str, help="Database file for Mendeley")
   parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
   parser.add_argument("--nonAPI", help="Runs code that doesn't use ADS API", action="store_true")
   parser.add_argument("--DOI", help="Updates DOI for all ArXiv papers", action="store_true")
   parser.add_argument("--arXiv", help="Check to see if any papers are on ArXiv", action="store_true")
   parser.add_argument("--abstract", help="Adds abstract for any paper missing it", action="store_true")
   parser.add_argument("--keyword", help="Adds author keywords", action="store_true")
   parser.add_argument("--pub", help="Adds publication info", action="store_true")
   parser.add_argument("--verify", help="Marks all altered papers for verification", action="store_true")
   parser.add_argument("--all", help="Runs DOI, arXiv, abstract, and publication updates", action="store_true")
   parser.add_argument("--start", help="Sets entry number to start on", type=int, default=1)
   args = parser.parse_args()
   if args.verbose:
      print "verbosity turned on"
   if args.nonAPI:
      print "run Non-API"
      nonAPI()
      sys.exit()
   if args.all:
      print "all ADS functions"
      args.DOI=True
      args.arXiv=True
      #args.keyword=True
      args.pub=True
      args.abstract=True
   if args.DOI:
      print "gets DOI"
   if args.arXiv:
      print "gets arXiv"
   if args.abstract:
      print "gets abstracts"
   if args.keyword:
      print "gets keywords"
   if args.pub:
      print "gets publication info"
   ADS_API()
   
