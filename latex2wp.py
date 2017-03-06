#!/bin/env python

import re
import argparse


# Style

PARAGRAPH_STYLE = 'text-align: justify'
MATHENV_STYLE = ('text-align: jusfity;'
                 'color: rgb(84, 84, 84);'
                 'font-family: Verdana,Helvetica,Arial,sans-serif;')


# Parser

def latex2wp():
    """Convert latex documents to HTML for Wordpress."""
    parser = argparse.ArgumentParser()
    parser.add_argument('input_path')
    #parser.add_argument('destination')
    args = parser.parse_args()

    source = None
    blocks = None
    paragraphs = []

    source = from_file(args.input_path)
    source = document(source)
    blocks = split_blocks(source)
    fragments = process(blocks)

    html = refs('\n'.join(fragments))
    print(html)


def from_file(path):
    with open(path, 'r') as source_file:
        return source_file.read()


def document(source):
    return re.search(r'\\begin{document}\n*(.*?)\n*\\end{document}',
                      source, re.S).group(1)


def split_blocks(source):
    return source.split('\n\n')


def process(blocks):
    fragments = []
    process = {
        '\\[': math_block_processor,
        '$': math_inline_processor,
        '\\begin{': command_processor
    }
    for block in blocks:
        for environ in ('$', '\\begin{', '\\['):  # TODO: Fix order
            if environ in block:
                block = process[environ](block)
        fragments.append('<p style="%s">%s</p>' % (PARAGRAPH_STYLE, block))
    return fragments


def math_block_processor(block):
    chunks = []
    for raw in re.split(r'(\\\[.*?\\\])', block, 0, re.S):
        if raw.startswith('\\['):
            chunk = raw.replace('\n', ' ')
            chunk = re.sub(r'(\\\[)(.*?)(\\\])',
                           (r'<p align=center>$latex \displaystyle \2'
                            '&fg=000000&bg=ffffff$</p>\n'), chunk)
        else:
            chunk = raw
        chunks.append(chunk)
    return ''.join(chunks)


def math_inline_processor(block):
    return re.sub(r'\$(.*?)\$', r'$latex {\1}&fg=000000&bg=ffffff$',
                  block, re.S)


def command_processor(block):
    match = re.search(r'\\begin{(\w+)}(\[([^\[\]\n]+)\])?(.*?)\\end{\w+}',
                      block, re.S)
    command = match.group(1)
    if command in ('array', 'aligned'):
        return block
    description = match.group(3)
    content = match.group(4)

    if 'lstlisting' == command:
        return lstlisting_environ(command, description, content)
    else:
        return math_environ(command, description, content)


def lstlisting_environ(command, description, content):
    return ('[code language="%s"]%s[/code]'
            % (description.split('=')[1], content))


def math_environ(command, description, content):
    caption = {
        'theorem': 'Teorema',
        'definition': 'Definición',
        'lemma': 'Lema',
        'proposition': 'Proposición',
        'corollary': 'Corolario',
        'axiom': 'Axioma',
        'claim': 'Afirmación',
        'remark': 'Observación',
        'example': 'Ejemplo',
        'exercise': 'Ejercicio',
        'conjecture': 'Conjetura'
    }
    math_environ.counter += 1
    content = label_command(content, str(math_environ.counter))
    return ('<blockquote style="%s"><b>%s %d%s.</b> %s</blockquote>'
            % (MATHENV_STYLE,
               caption[command],
               math_environ.counter,
               (' <em>(%s)</em>' % description) if description else '',
               content.strip()))

math_environ.counter = 0


def label_command(content, tag):
    label_match = re.search(r'\\label{(\w+)}', content)
    if label_match:
        for label in label_match.groups():
            label_command.tag[label] = tag
        content = re.sub(r'\\label{(\w+)}\n?', r'<a name="\1"></a>', content)
    return content

label_command.tag = {}


def refs(text):
    for label, tag in label_command.tag.items():
        text = text.replace('\\ref{%s}' % label,
                            '<a href="#%s">%s</a>' % (label, tag))
    return text


if '__main__' == __name__:
    latex2wp()
