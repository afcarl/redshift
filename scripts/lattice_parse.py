#!/usr/bin/env python

import plac
from pathlib import Path
import math

import redshift.parser
from redshift.sentence import Input
from redshift.lattice_utils import read_lattice, add_gold_parse
from redshift.lattice_utils import levenshtein


def get_gold_lattice(conll_str, asr_dir):
    gold_sent = Input.from_conll(conll_str)
    turn_id = gold_sent.turn_id
    filename, turn_num = gold_sent.turn_id.split('~')
    speaker = turn_num[0]
    turn_num = turn_num[1:]
    turn_id = '%s%s~%s' % (filename, speaker, turn_num)
    lattice_loc = asr_dir.join(filename).join(speaker).join('raw').join(turn_id)
    if lattice_loc.exists(): 
        lattice = read_lattice(str(lattice_loc), add_gold=True)
        add_gold_parse(lattice, gold_sent)
        return lattice
    else:
        return None
    

def sparseval(test, gold):
    test_deps = _get_deps(test)
    gold_deps = _get_deps(gold)
    tp = test_deps.intersection(gold_deps)
    fn = gold_deps - test_deps
    return len(tp), len(fn), len(test_deps)


def _get_deps(tokens):
    deps = set()
    n = len(tokens)
    for t in tokens:
        if t.is_edit:
            continue
        head = tokens[t.head - 1].word if (t.head - 1) < n else "ROOT"
        deps.add((t.word, head))
    return deps


@plac.annotations(
)
def main(parser_dir, conll_loc, asr_dir):
    asr_dir = Path(asr_dir)
    print "Get sents"
    sents = [get_gold_lattice(s, asr_dir) for s in
             open(conll_loc).read().strip().split('\n\n') if s.strip()]
    sents = [s for s in sents if s is not None]
    print len(sents)
    print "Loading parser"
    parser = redshift.parser.Parser(parser_dir)
    wer = 0
    n = 0
    bl_wer = 0
    vn = 0
    tp_deps = 0
    fn_deps = 0
    n_deps = 0
    for sent in sents:
        asr_tokens = list(t.word for t in sent.lattice_baseline_tokens)
        gold_tokens = list(sent.tokens)
        gold_verbatim_tokens = list([t.word for t in gold_tokens if t.word != '*DELETE*'])
        parser.parse(sent)
        guess_tokens = list(sent.tokens)
        parse_scores = sparseval(guess_tokens, gold_tokens)
        tp_deps += parse_scores[0]
        fn_deps += parse_scores[1]
        n_deps += parse_scores[2]
        fluent_gold = [t.word for t in gold_tokens if not t.is_edit]
        fluent_guess = [t.word for t in guess_tokens if not t.is_edit]
        wer += levenshtein(fluent_guess, fluent_gold)
        bl_wer += levenshtein(asr_tokens, gold_verbatim_tokens)
        n += len(fluent_gold)
        vn += len(gold_verbatim_tokens)
    print "Against verbatim:"
    print "Acoustic 1: %.3f" % (float(bl_wer) / vn)
    print "Against fluent:"
    print 'Hyp: %.3f' % (float(wer) / n)
    print "Sparseval:"
    p = float(tp_deps) / n_deps
    r = float(tp_deps) / (tp_deps + fn_deps)
    print "P: %.3f" % p
    print "R: %.3f" % r
    print "F: %.3f" % ((2 * p * r) / (p + r))


if __name__ == "__main__":
    plac.call(main)