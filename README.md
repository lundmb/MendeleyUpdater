 MendeleyUpdater
Updates Mendeley sqlite by checking for DOI numbers for arXiv papers

===================================================================================
 FILE: MendeleyUpdate.py

 USAGE: ./MendeleyUpdate.py [FILE]

 DESCRIPTION: Updates Menedley Database.
 Checks for all entries that have an arXiv ID but not a DOI.
 Queries the SAO/NASA Astrophysics Data System to check for assigned DOI.
 If DOI is available, updates sqlite database and moves entry to 'Needs Review'.
 To update full article information, use Mendeley for DOI lookup.

 OPTIONS: ---
 REQUIREMENTS: ---
 BUGS: ---
 NOTES: ---
 AUTHOR: Michael Lund, Mike.Lund@gmail.com
 COMPANY: ---
 VERSION: 1.0
 CREATED: 23.05.2015 - 20:52:00
 REVISION: ---
===================================================================================
