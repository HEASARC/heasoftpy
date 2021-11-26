

import sys
import os
import subprocess

if __name__ == '__main__':
    # this will be updated depending on where we want this installed
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from heasoftpy.core import HSPTask, HSPTaskException
    from heasoftpy.utils import process_cmdLine
else:    
    from ..core import HSPTask, HSPTaskException



def ftlist(args=None, **kwargs):
    r"""

    Automatically generated function for Heasoft task ftlist.
    Additional help may be provided below.

    Args:
     infile       (Req) : Input file name  (default: ../tests/test.fits)
     option       (Req) : Print options: H C K I T  (default: T)
     outfile            : Optional output file  (default: -)
     clobber            : Overwrite existing output file?  (default: no)
     include            : Include keywords list  (default: *)
     exclude            : Exclude keywords list  (default: )
     section            : Image section to print (default: *)
     columns            : Table columns to print  (default: *)
     rows               : Table rows or ranges to print (default: -)
     vector             : Vector range to print (default: -)
     separator          : Column separator string  (default:  )
     rownum             : Print row number?  (default: no)
     colheader          : Print column header?  (default: no)
     mode               : Mode  (default: ql)



--------------------------------------------------
   The following has been generated from fhelp
--------------------------------------------------
NAME

   ftlist - List the contents of the input file.

USAGE

   ftlist infile[ext][filters] option

DESCRIPTION

   'ftlist' displays the contents of the input file. Depending on the
   value of the 'option' parameter, this task can be used to list any
   combination of the following:

     * a one line summary of the contents of each HDU (option = H)
     * the names, units, and ranges of each table column (option = C)
     * all or a selected subset of the header keywords (option = K)
     * the pixel values in a subset of an image (option = I)
     * the values in selected rows and columns of a table (option = T)

   If a specific HDU name or number is given as part of the input file
   name then only that HDU will be listed. If only the root name of the
   file is specified, then every HDU in the file will be listed.

PARAMETERS

   infile [filename]
          Input file name and optional extension name or number enclosed
          in square brackets of the file or HDU to be displayed. If a
          specific HDU is not given, then all the HDUs in the file will be
          displayed. Additional virtual file filters can be appended to
          the file name, as shown in some of the examples, to modify the
          amount of information that is display.

   option [string]
          The option parameter controls the type of information to
          display. The string may consist of any combination of the
          characters H, C, K, I, and/or T, where,

         H lists a 1-line summary of the HDU,
         C lists the names and units of Columns in a table,
         K lists the Keywords,
         I lists Image pixel values, and
         T lists the element values in rows and columns of a Table.

          By default the K, I, and T options display, respectively, all
          the keywords, image pixels or table elements in the HDU. These
          options can be modified to display only a restricted range of
          values by using the additional parameters described below.

   (outfile = "-") [filename]
          Name of optional text file where the output listing will be
          sent. If 'outfile' = "-", "stdout", "STDOUT", or a blank string,
          then the output will be sent to the stdout stream. If the name
          is preceded by an '!' (or '\!' on the Unix command line), then
          any existing file with that name will be overwritten by the new
          file.

   (clobber = No) [boolean]
          If outfile already exists, then setting "clobber = yes" will
          cause it to be overwritten.

   (include = "*") [string]
          When listing header keywords (with option = 'K') the 'include'
          parameter contains a comma separated list of the keywords to be
          displayed. The wild card characters (?, *, and #) may be used in
          the names, where '?' will match any single character, '*'
          matches any string of characters (including zero characters) and
          '#' matches a string of decimal digits. The default value, '*',
          will display every keyword. For example, include =
          'p*,naxis#,?zero*' will display all keywords beginning with 'P',
          plus all keywords beginning with 'NAXIS' and followed by one or
          more digits, plus all the keywords that have the string 'ZERO'
          as the 2nd through 5th characters of the keyword name.

   (exclude = "") [string]
          When listing header keywords (with option = 'K') the 'exclude'
          parameter contains an optional comma separated list of keyword
          names that should not be displayed, even if they match one of
          the 'include' keyword names . Wildcard characters may be used in
          the list as described for the 'include' parameter. For example,
          include='C*' and exclude='COMMENT' will list all the keywords
          beginning with C except the COMMENT keywords.

   (section = "*:*") [string]
          When listing the pixel values in an image (with option = 'I'),
          the 'section' parameter specifies the range of row and columns
          in the image to display. By default the entire image will be
          listed, but this is probably not useful in most cases because
          the long output lines will simply wrap around on the display.
          The image section format is "xmin:xmax,ymin:ymax". For example,
          "30:35,40:50" will display the pixel values in columns 30 - 35
          and rows 40 - 50 of the image.

   (columns = "*") [string]
          When listing the contents of FITS tables (with option = 'T') the
          'columns' parameter gives a comma separated list of the columns
          in the table to be displayed. Either the column name or the
          columun number (beginning with 1 for the first column in the
          table) may be listed; The column names are not case-sensitive.
          The columns will be displayed in the order that they are given
          in this list. If a column name in the list does not exist in the
          table, it will be ignored.

          The wildcard characters (?, *, and #) may be used in the names
          to match more than one column, as described for the 'include'
          parameter. For example, 'columns=?sky' will list all the columns
          whose names are 4 characters long and end with the string 'sky'.
          The default value, '*', will display all the columns in the
          table.

          The simplest way to display all but a small number of columns in
          the table is to use the '[col]' virtual filename filter to list
          the excluded columns, preceded by a minus sign. For example, if
          infile = 'file.fits[col -ACOL;-BCOL]' then all the columns in
          the table except the columns named 'ACOL' and 'BCOL' will be
          displayed.

   (rows = "-") [string]
          When listing the contents of FITS tables (with option = 'T') the
          'rows' parameter gives a comma separated list of rows or row
          ranges in the table to be displayed. For example, "2,4,8-12"
          will display the table element values in rows 2, 4, and rows 8
          through 12 of the table, and "50-" will display rows 50 and
          higher. The row numbers must be specified in ascending order and
          the ranges must not overlap. By default, all rows are displayed.

   (vector = "-") [string]
          When listing the contents of vector columns in binary tables
          (with option = "T"), the 'vector' parameter gives the range of
          elements in the vector to display. For example, vector=1-5 will
          list the first 5 elements. By default, all elements are
          displayed. Bit columns, (e.g., with TFORMn = '32X') are a
          special case and are displayed as a string of 1s or 0s, 8 bits
          per line. In this case, 'vector=1-2' would display the first 16
          bits in the vector.

   (separator = " ") [string]
          When listing image pixel values (option = 'I') or table elements
          (option = 'T'), the string given by the separator parameter will
          be inserted between each column. By default, the columns will be
          separated by a space character.

   (rownum = "Yes") [boolean]
          If rownum = "Yes", then the row number will be listed at the
          beginning of each row when displaying image pixels (option =
          'I') or table data (option = 'T').

   (colheader = "Yes") [boolean]
          If colheader = "Yes", a header will be listed at the top of each
          column when displaying image pixels (option = 'I') or table data
          (option = 'T'). The header consists of the column number in the
          case of images, and the column name and units in the case of
          tables.

EXAMPLES

   Note that when commands are issued on the Unix command line, strings
   containing special characters such as '[' or ']' must be enclosed in
   single or double quotes.

   1. Print out summary information about each HDU in the input file (the
   'H' option), and a list of the columns in each table HDU (the 'C'
   option).

      ftlist infile.fits hc

   2. Print out the HDU summary (H option) and the header keywords (K
   option) in the input file. The first example lists all the keywords in
   the all the HDUs in the file. The second example lists only the COMMENT
   and HISTORY keywords in the 2nd HDU in the file. The 3rd example lists
   all the keyword beginning with the letter 'C', excluding the COMMENT
   keywords.

      ftlist infile.fits hk

      ftlist infile.fits+1 hk include='comment,history'

      ftlist infile.fits+1 hk include='c*' exclude='COMMENT'

   3. Print out summary HDU information, a list of columns in the table,
   and the element values in the tables. The first example lists the
   entire contents of all the table HDUs in the file. The 2nd example
   lists only rows 1 through 20 of the X and Y columns in the EVENTS
   extension. The 3rd example is similar, except it lists the 1st and 3rd
   columns in the table. The 4th example lists all the columns except the
   'time' column, and only displays the first two elements of each vector
   column.

      ftlist infile.fits hct

      ftlist 'infile.fits[events]' hct rows=1-20 columns=x,y

      ftlist 'infile.fits[events]' hct rows=1-20 columns=1,3

      ftlist 'infile.fits[col -time]' hct vector=1-2


   4. Dump all the row and columns in the EVENTS table to the out.fits
   file; the values are separated by a comma, and no column headers or row
   numbers are printed.

      ftlist 'infile.fits[events] t outfile=out.fits separator=', '
              rownum=no colheader=no


   5. Print out the image pixel values for columns 50 through 55 and rows
   20 through 40 in the input image, suppressing the column headers and
   row numbers.

      ftlist image.fits i section=50:55,20:40 colheader=no rownum=no

SEE ALSO

   filenames, imfilter, colfilter, rowfilter, binfilter,

   fv, the interactive FITS file editor, can also be used to view the
   contents of FITS files.

   The design of this task is based on the fdump, fstruct, flcol,
   fkeyprint, flist, and fimgdmp tasks in the ftools package and the
   dmlist task in the CXC CIAO package.

LAST MODIFIED

   April 2002

        
    """

    ftlist_task = HSPTask(name="ftlist")
    return ftlist_task(args, **kwargs)


if __name__ == '__main__':
    ftlist_task = HSPTask(name="ftlist")
    cmd_args = process_cmdLine(ftlist_task)
    ftlist_task(**cmd_args)

        