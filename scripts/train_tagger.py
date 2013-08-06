import plac
import time

import redshift.tagger
import redshift.io_parse

@plac.annotations(
    iters=("Number of training iterations", "option", "i", int),
    n_sents=("Number of training sentences", "option", "n", int),
)
def main(model_loc, train_loc, test_loc, iters=5, n_sents=0):
    tagger = redshift.tagger.BeamTagger(model_loc, clean=True)
    train_strs = open(train_loc).read().strip().split('\n')
    # Apply limit
    train_strs = train_strs[-n_sents:]
    train = redshift.io_parse.read_pos('\n'.join(train_strs), sep='|')
    tagger.train(train, nr_iter=iters)
    tagger.save()
    test_data = open(test_loc).read()
    to_tag = redshift.io_parse.read_pos(test_data, sep='|')
    t1 = time.time()
    tagger.add_tags(to_tag)
    t2 = time.time()
    print '%d sents took %0.3f ms' % (to_tag.length, (t2-t1)*1000.0)
    gold = redshift.io_parse.read_pos(test_data, sep='|')
    acc, c, n = redshift.io_parse.eval_tags(to_tag, gold)
    print '%.2f' % acc, c, n

if __name__ == '__main__':
    plac.call(main)
