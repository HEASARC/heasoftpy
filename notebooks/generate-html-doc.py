helptxt="""Generate html pages with css styles for the website.

For notebooks, use jupyter-nbconvert and for markdown,
put it in a notebook and then use jupyter-nbconvert

Output will be put in file-name.html 

"""

import os
import sys



# minimum md to ipynb template
ipynb_template = """
{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "72bf1fc3-992b-46a8-b94c-5044fe79a9d9",
   "metadata": {},
   "outputs": [],
   "source": [
    "from IPython.display import Markdown, display\\n",
    "display(Markdown(\\"%s\\"))"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.9.7"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
"""


# simple converter from .md to .ipynb
def convert_file(file):
    """convert a .md or .ipynb file to html
    
    if the file is markdown (.md), first convert it to .ipynb
    
    Arguments:
        file: name of the file
    
    """
    
    base_name, ext = file.split('/')[-1].split('.')

    
    if not ext in ['md', 'ipynb']:
        raise ValueError('This is script only handle .md and .ipynb files')
        
    # convert md to ipynb
    if ext == 'md':
        
        with open(f'{base_name}.ipynb', 'w') as fp:
            fp.write(ipynb_template%file)
            
    
    # run jupyter-nbonvert
    extra_arg = '--no-input' if ext == 'md' else ''
    cmd = f'jupyter nbconvert --to html --execute {extra_arg} {base_name}.ipynb'
    os.system(cmd)
    
    if ext == 'md':
        os.system(f'rm -f {base_name}.ipynb')
        

        
if __name__ == '__main__':
    
    if len(sys.argv) == 1:
        print(f'----------\n{helptxt}----------')
        print('\n** No file name given.**\nUSAGE: python generate-html-doc.py file-name\n'
              'where file-name is either a markdown (.md) or a notebook (.ipynb) file\n\n')
        exit(1)
        
    files = sys.argv[1:]
    
    for file in files:
        convert_file(file)
