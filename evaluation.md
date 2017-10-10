# Evaluation

* What does it _mean_ to evaluate an unsupervised algorithm?
  * Normally we would compare against ground truth, but we have none
  * 'interestingness' - how strongly does it cluster
  * 'which of these is not like the other'
    * find sets of A, B, C such that we expect A and B to be similar but C to be dissimilar (e.g. AB share department or advisor, C is different department or randomly chosen)
    * Use DocVecsArray.doesnt_match
    * Count successes
  * Evaluate word vectors
    * https://cs.stanford.edu/~angeli/papers/2016-acl-veceval.pdf
      * "Schnabel et al. (2015) carried out both a thorough intrinsic evaluation of word vectors, and a limited extrinsic evaluation showing that an embedding’s intrinsic performance did not necessarily correlate with its real-world performance."
    * http://www.wordvectors.org/ for intrinsic evaluation
    * look for veceval.com script (site is gone)
  * DON'T use author-assigned keywords from dspace
    * many of them correspond to only one thesis
    * so we can't use those to group similar theses together
