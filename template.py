from curses import keyname
from curses.ascii import isalpha
import enum
from math import gamma
import math
from sre_parse import State
from turtle import back
import nltk, inspect, sys, hashlib

from nltk.corpus import brown

# module for computing a Conditional Frequency Distribution
from nltk.probability import ConditionalFreqDist

# module for computing a Conditional Probability Distribution
from nltk.probability import ConditionalProbDist, LidstoneProbDist

from nltk.tag import map_tag

from adrive2 import trim_and_warn

assert map_tag('brown', 'universal', 'NR-TL') == 'NOUN', '''
Brown-to-Universal POS tag map is out of date.'''


class HMM:
    def __init__(self, train_data):
        """
        Initialise a new instance of the HMM.

        :param train_data: The training dataset, a list of sentences with tags
        :type train_data: list(list(tuple(str,str)))
        """
        self.train_data = train_data

        # Emission and transition probability distributions
        self.emission_PD = None
        self.transition_PD = None
        self.states = []
        self.viterbi = []
        self.backpointer = []

    # Q1

    # Compute emission model using ConditionalProbDist with a LidstoneProbDist estimator.
    #   To achieve the latter, pass a function
    #    as the probdist_factory argument to ConditionalProbDist.
    #   This function should take 3 arguments
    #    and return a LidstoneProbDist initialised with +0.001 as gamma and an extra bin.
    #   See the documentation/help for ConditionalProbDist to see what arguments the
    #    probdist_factory function is called with.
    def emission_model(self, train_data):
        """Compute an emission model based on labelled training data.
        Don't forget to lowercase the observation otherwise it mismatches the test data.

        :param train_data: The training dataset, a list of sentences with tags
        :type train_data: list(list(tuple(str,str)))
        :return: The emission probability distribution and a list of the states
        :rtype: Tuple[ConditionalProbDist, list(str)]
        """
        # TODO prepare data
        # Don't forget to lowercase the observation otherwise it mismatches the test data
        # Do NOT add <s> or </s> to the input sentences
        tagged_words = [(tup[0].lower(), tup[1]) for el in train_data for tup in el]

        # TODO compute the emission model
        emission_FD = ConditionalFreqDist()
        states = []
        for tw in tagged_words:
            emission_FD[tw[1]][tw[0]] += 1
            states.append(tw[1])

        estimator = lambda fdist: LidstoneProbDist(fdist, 0.001, bins=fdist.B()+1)
        self.emission_PD = ConditionalProbDist(emission_FD, estimator)
        self.states = list(set(states))

        return self.emission_PD, self.states

    # Q1

    # Access function for testing the emission model
    # For example model.elprob('VERB','is') might be -1.4
    def elprob(self, state, word):
        """
        The log of the estimated probability of emitting a word from a state

        :param state: the state name
        :type state: str
        :param word: the word
        :type word: str
        :return: log base 2 of the estimated emission probability
        :rtype: float
        """
        return self.emission_PD[state].logprob(word)


    # Q2
    # Compute transition model using ConditionalProbDist with the same
    #  estimator as above (but without the extra bin)
    # See comments for emission_model above for details on the estimator.
    def transition_model(self, train_data):
        """
        Compute a transition model using a ConditionalProbDist based on
          labelled data.

        :param train_data: The training dataset, a list of sentences with tags
        :type train_data: list(list(tuple(str,str)))
        :return: The transition probability distribution
        :rtype: ConditionalProbDist
        """
        # TODO: prepare the data
        # The data object should be an array of tuples of conditions and observations,
        # in our case the tuples will be of the form (tag_(i),tag_(i+1)).
        # DON'T FORGET TO ADD THE START SYMBOL </s> and the END SYMBOL </s>
        #print(train_data[0:10])
        tagged_sents = [[("<s>","<s>")] + el + [("</s>","</s>")] for el in train_data]

        # TODO compute the transition model
        transition_FD = ConditionalFreqDist()
        for ts in tagged_sents:
            for i, tagged_word in enumerate(ts):
                if i < len(ts)-1:
                    next_tagged_word = ts[i+1]
                    transition_FD[tagged_word[1]][next_tagged_word[1]] += 1

        estimator = lambda fdist: LidstoneProbDist(fdist, gamma=0.001, bins=fdist.B())
        self.transition_PD = ConditionalProbDist(transition_FD, estimator)

        return self.transition_PD

    # Q2
    # Access function for testing the transition model
    # For example model.tlprob('VERB','VERB') might be -2.4
    def tlprob(self, state1, state2):
        """
        The log of the estimated probability of a transition from one state to another

        :param state1: the first state name
        :type state1: str
        :param state2: the second state name
        :type state2: str
        :return: log base 2 of the estimated transition probability
        :rtype: float
        """
        return self.transition_PD[state1].logprob(state2)

    # Train the HMM
    def train(self):
        """
        Trains the HMM from the training data
        """
        self.emission_model(self.train_data)
        self.transition_model(self.train_data)

    # Part B: Implementing the Viterbi algorithm.

    # Q3
    # Initialise data structures for tagging a new sentence.
    # Describe the data structures with comments.
    # Use the models stored in the variables: self.emission_PD and self.transition_PD
    # Input: first word in the sentence to tag and the total number of observations.
    def initialise(self, observation, number_of_observations):
        """
        Initialise data structures self.viterbi and self.backpointer for tagging a new sentence.

        :param observation: the first word in the sentence to tag
        :type observation: str
        :param number_of_observations: the number of observations
        :type number_of_observations: int
        """
        # Initialise step 0 of viterbi, including
        #  transition from <s> to observation
        # use costs (- log-base-2 probabilities)
        # TODO
        viterbi = {i: {} for i in range(number_of_observations)}
        backpointer = [{} for _ in range(number_of_observations)]

        min_state = ""
        min_cost = 1e+10
        for state in self.states:
            #prior = state_counts[s]/len(self.states) #number_of_observations/len(self.train_data)
            trans = -self.transition_PD["<s>"].logprob(state)
            #emis = -self.emission_PD[state].logprob(observation)
            cost = trans #+ emis
            #print(state)
            #print(prob)
            #print()
            if cost < min_cost:
                min_state = state
                min_cost = cost

            viterbi[0][state] = cost - self.emission_PD[state].logprob(observation)
            #backpointer[0]
            #backpointer.append(0)

        self.viterbi = viterbi
        #print(viterbi[0]["DET"])

        # Initialise step 0 of backpointer
        # TODO
        backpointer[0][min_state] = "<s>"
        self.backpointer = backpointer

    # Q3
    # Access function for testing the viterbi data structure
    # For example model.get_viterbi_value('VERB',2) might be 6.42
    def get_viterbi_value(self, state, step):
        """
        Return the current value from self.viterbi for
        the state (tag) at a given step

        :param state: A tag name
        :type state: str
        :param step: The (0-origin) number of a step:  if negative,
          counting backwards from the end, i.e. -1 means the last step
        :type step: int
        :return: The value (a cost) for state as of step
        :rtype: float
        """
        pos_step = step
        if pos_step < 0:
            pos_step += len(self.viterbi)
        #if not pos_step in self.viterbi.keys():
        #    print(self.viterbi)
        return self.viterbi[pos_step][state]

    # Q3
    # Access function for testing the backpointer data structure
    # For example model.get_backpointer_value('VERB',2) might be 'NOUN'
    def get_backpointer_value(self, state, step):
        """
        Return the current backpointer from self.backpointer for
        the state (tag) at a given step

        :param state: A tag name
        :type state: str
        :param step: The (0-origin) number of a step:  if negative,
          counting backwards from the end, i.e. -1 means the last step
        :type step: int
        :return: The state name to go back to at step-1
        :rtype: str
        """
        #print(self.backpointer[state])
        pos_step = step
        if pos_step < 0:
            pos_step += len(self.backpointer)
        #print(pos_step)
        #print(len(self.backpointer))
        #print(state)
        #print(self.backpointer)
        #print()
        return self.backpointer[pos_step][state]


    # Q4a
    # Tag a new sentence using the trained model and already initialised data structures.
    # Use the models stored in the variables: self.emission_PD and self.transition_PD.
    # Update the self.viterbi and self.backpointer data structures.
    # Describe your implementation with comments.
    def tag(self, observations):
        """
        Tag a new sentence using the trained model and already initialised data structures.

        :param observations: List of words (a sentence) to be tagged
        :type observations: list(str)
        :return: List of tags corresponding to each word of the input
        """
        tags = []
        self.initialise(observations[0], len(observations))
        last_state = list(self.backpointer[0].keys())[0]
        step = -1
        #print(observations)
        for step, word in enumerate(observations[1:]):
            word = word.lower()

            for dest_state in self.states:
                state_costs = {}

                for ori_state in self.states:
                    state_costs[ori_state] = self.get_viterbi_value(ori_state, step) - self.transition_PD[ori_state].logprob(dest_state)
                    #if ori_state == last_state:
                    #    self.backpointer[step][dest_state] = ori_state

                min_cost_key = min(state_costs, key=state_costs.get)
                min_cost = state_costs[min_cost_key]

                self.viterbi[step+1][dest_state] = min_cost - self.emission_PD[dest_state].logprob(word)
                self.backpointer[step+1][dest_state] = min_cost_key

            last_state = min(self.viterbi[step+1], key=self.viterbi[step+1].get)

        # TODO
        # Add a termination step with cost based solely on cost of transition to </s> , end of sentence.
        dest_state = "</s>"
        state_costs = {}
        #print("new")
        #print(observations)
        for ori_state in self.states:
            #print(step)
            state_costs[ori_state] = self.get_viterbi_value(ori_state, step+1) - self.transition_PD[ori_state].logprob(dest_state)
            #if ori_state == last_state:
                #self.backpointer[step+1][dest_state] = ori_state

        min_cost_key = min(state_costs, key=state_costs.get)
        min_cost = state_costs[min_cost_key]

        #self.viterbi[step+2][dest_state] = min_cost
        #self.backpointer[step+2][dest_state] = min_cost_key
        #print(self.backpointer)
        #breakpoint()

        #print(self.viterbi[len(observations)-1])
        #breakpoint()
        """
        state_costs = {}
        for state in self.states:
            state_costs[state] = self.get_viterbi_value(state, step+1) - self.transition_PD[state].logprob("</s>")
            if state == last_state:
                self.backpointer[step+2]["</s>"] = state
            
        min_state = min(state_costs, key=state_costs.get)
        self.viterbi[step+2]["</s>"] = state_costs[min_state]
        self.backpointer[step+2]["</s>"] = min_state
        """
        # TODO
        # Reconstruct the tag sequence using the backpointers.
        # Return the tag sequence corresponding to the best path as a list.
        # The order should match that of the words in the sentence.
        tags = [min_cost_key]
        #print(self.backpointer)
        #breakpoint()
        bp = self.backpointer.copy()
        #print(bp)
        bp.reverse()
        bp = bp[:-1]
        #print(bp)
        #breakpoint()

        for i, points in enumerate(bp):
            #print(points)
            #print(tags[0])
            #print()
            step = len(observations) - i
            next_state = points[tags[0]]
            tags = [next_state] + tags

            #if len(tags) == len(observations):
            #    break
        #print(tags)
        #print(self.viterbi)
        #print(len(self.backpointer))
        #print(self.backpointer)
        #breakpoint()
        #self.viterbi = {key: self.viterbi[key] for key in list(self.viterbi.keys()) if key > 0 and key < len(observations)}
        #print(list(zip(tags, observations)))

        return tags

    def tag_sentence(self, sentence):
        """
        Initialise the HMM, lower case and tag a sentence. Returns a list of tags.
        :param sentence: the sentence
        :type sentence: list(str)
        :rtype: list(str)
        """
        return self.tag(sentence)



def answer_question4b():
    """
    Report a hand-chosen tagged sequence that is incorrect, correct it
    and discuss
    :rtype: list(tuple(str,str)), list(tuple(str,str)), str
    :return: incorrectly tagged sequence, correctly tagged sequence and your answer [max 280 chars]
    """
    #raise NotImplementedError('answer_question4b')

    # One sentence, i.e. a list of word/tag pairs, in two versions
    #  1) As tagged by your HMM
    #  2) With wrong tags corrected by hand
    tagged_sequence = [('the', 'DET'), ('elf', 'ADJ'), ('was', 'VERB'), ('on', 'ADP'), ('the', 'DET'), ('shelf', 'ADJ')]
    correct_sequence = [('the', 'DET'), ('elf', 'NOUN'), ('was', 'VERB'), ('on', 'ADP'), ('the', 'DET'), ('shelf', 'NOUN')]
    # Why do you think the tagger tagged this example incorrectly?
    answer = inspect.cleandoc("""\
    The tagger tagged this example incorrectly as \"elf\" and \"shelf\" both did not appear
    in any sentences in the training set. This ultimately means the tagger sets the base
    probabilities """)

    return tagged_sequence, correct_sequence, trim_and_warn("Q4a", 280, answer)


# Q5a
def hard_em(labeled_data, unlabeled_data, k):
    """
    Run k iterations of hard EM on the labeled and unlabeled data.
    Follow the pseudo-code in the coursework instructions.

    :param labeled_data:
    :param unlabeled_data:
    :param k: number of iterations
    :type k: int
    :return: HMM model trained with hard EM.
    :rtype: HMM
    """
    raise NotImplementedError()
    return ... # fix me


def answer_question5b():
    """
    Sentence:  In    fact  he    seemed   delighted  to  get   rid  of  them   .
    Gold POS:  ADP   NOUN  PRON  VERB     VERB      PRT  VERB  ADJ  ADP  PRON  .
    T_0     :  PRON  VERB  NUM    ADP     ADJ       PRT  VERB  NUM  ADP  PRON  .
    T_k     :  PRON  VERB  PRON  VERB     ADJ       PRT  VERB  NUM  ADP  NOUN  .

    1) T_0 erroneously tagged "he" as "NUM" and T_k correctly identifies it as "PRON".
        Speculate why additional unlabeled data might have helped in that case.
        Refer to the training data (inspect the 20 sentences!).
    2) Where does T_k mislabel a word but T_0 is correct? Why do you think did hard EM hurt in that case?

    :rtype: str
    :return: your answer [max 500 chars]
    """
    raise NotImplementedError('answer_question5b')

    return trim_and_warn("Q5b", 500, inspect.cleandoc("""your answer"""))



def answer_question6():
    """
    Suppose you have a hand-crafted grammar that has 100% coverage on
        constructions but less than 100% lexical coverage.
        How could you use a POS tagger to ensure that the grammar
        produces a parse for any well-formed sentence,
        even when it doesn't recognise the words within that sentence?

    :rtype: str
    :return: your answer [max 500 chars]
    """
    raise NotImplementedError('answer_question6')

    return trim_and_warn("Q6", 500, inspect.cleandoc("""
    your answer"""))


def answer_question7():
    """
    Why else, besides the speedup already mentioned above, do you think we
    converted the original Brown Corpus tagset to the Universal tagset?
    What do you predict would happen if we hadn't done that?  Why?

    :rtype: str
    :return: your answer [max 500 chars]
    """
    raise NotImplementedError('answer_question7')

    return trim_and_warn("Q7", 500, inspect.cleandoc("""\
    your answer"""))


def compute_acc(hmm, test_data, print_mistakes):
    """
    Computes accuracy (0.0 - 1.0) of model on some data.
    :param hmm: the HMM
    :type hmm: HMM
    :param test_data: the data to compute accuracy on.
    :type test_data: list(list(tuple(str, str)))
    :param print_mistakes: whether to print the first 10 model mistakes
    :type print_mistakes: bool
    :return: float
    """
    # TODO: modify this to print the first 10 sentences with at least one mistake if print_mistakes = True
    correct = 0
    incorrect = 0
    for sentence in test_data:
        s = [word for (word, tag) in sentence]
        tags = hmm.tag_sentence(s)

        for ((word, gold), tag) in zip(sentence, tags):
            if tag == gold:
                correct += 1
            else:
                incorrect += 1

    return float(correct) / (correct + incorrect)


# Useful for testing
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    # http://stackoverflow.com/a/33024979
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def answers():
    global tagged_sentences_universal, test_data_universal, \
        train_data_universal, model, test_size, train_size, ttags, \
        correct, incorrect, accuracy, \
        good_tags, bad_tags, answer4b, answer5, answer6, answer7, answer5b, \
        t0_acc, tk_acc

    # Load the Brown corpus with the Universal tag set.
    tagged_sentences_universal = brown.tagged_sents(categories='news', tagset='universal')

    # Divide corpus into train and test data.
    test_size = 500
    train_size = len(tagged_sentences_universal) - test_size

    # tail test set
    test_data_universal = tagged_sentences_universal[-test_size:]  # [:test_size]
    train_data_universal = tagged_sentences_universal[:train_size]  # [test_size:]
    if hashlib.md5(''.join(map(lambda x: x[0],
                               train_data_universal[0] + train_data_universal[-1] + test_data_universal[0] +
                               test_data_universal[-1])).encode(
            'utf-8')).hexdigest() != '164179b8e679e96b2d7ff7d360b75735':
        print('!!!test/train split (%s/%s) incorrect -- this should not happen, please contact a TA !!!' % (
        len(train_data_universal), len(test_data_universal)), file=sys.stderr)

    # Create instance of HMM class and initialise the training set.
    model = HMM(train_data_universal)

    # Train the HMM.
    model.train()

    # Some preliminary sanity checks
    # Use these as a model for other checks
    e_sample = model.elprob('VERB', 'is')
    if not (type(e_sample) == float and e_sample <= 0.0):
        print('elprob value (%s) must be a log probability' % e_sample, file=sys.stderr)

    t_sample = model.tlprob('VERB', 'VERB')
    if not (type(t_sample) == float and t_sample <= 0.0):
        print('tlprob value (%s) must be a log probability' % t_sample, file=sys.stderr)

    if not (type(model.states) == list and \
            len(model.states) > 0 and \
            type(model.states[0]) == str):
        print('model.states value (%s) must be a non-empty list of strings' % model.states, file=sys.stderr)

    #print('states: %s\n' % model.states)

    ######
    # Try the model, and test its accuracy [won't do anything useful
    #  until you've filled in the tag method
    ######
    s = 'the cat in the hat came back'.split()
    ttags = model.tag_sentence(s)
    print("Tagged a trial sentence:\n  %s" % list(zip(s, ttags)))

    s2 = "the elf was on the shelf".split()
    tags2 = model.tag_sentence(s2)
    print("Tagged a trial sentence:\n  %s" % list(zip(s2, tags2)))

    v_sample = model.get_viterbi_value('VERB', 5)
    if not (type(v_sample) == float and 0.0 <= v_sample):
        print('viterbi value (%s) must be a cost' % v_sample, file=sys.stderr)

    b_sample = model.get_backpointer_value('VERB', 5)
    if not (type(b_sample) == str and b_sample in model.states):
        print('backpointer value (%s) must be a state name' % b_sample, file=sys.stderr)

    # check the model's accuracy (% correct) using the test set
    accuracy = compute_acc(model, test_data_universal, print_mistakes=True)
    print('\nTagging accuracy for test set of %s sentences: %.4f' % (test_size, accuracy))

    #Tag the sentence again to put the results in memory for automarker.
    model.tag_sentence(s)

    # Question 5a
    # Set aside the first 20 sentences of the training set
    num_sentences = 20
    semi_supervised_labeled = train_data_universal[:num_sentences]  # type list(list(tuple(str, str)))
    semi_supervised_unlabeled = [[word for (word, tag) in sent] for sent in train_data_universal[num_sentences:]]  # type list(list(str))
    print("Running hard EM for Q5a. This may take a while...")
    t0 = hard_em(semi_supervised_labeled, semi_supervised_unlabeled, 0) # 0 iterations
    tk = hard_em(semi_supervised_labeled, semi_supervised_unlabeled, 3)
    print("done.")

    t0_acc = compute_acc(t0, test_data_universal, print_mistakes=False)
    tk_acc = compute_acc(tk, test_data_universal, print_mistakes=False)
    print('\nTagging accuracy of T_0: %.4f' % (t0_acc))
    print('\nTagging accuracy of T_k: %.4f' % (tk_acc))
    ########

    # Print answers for 4b, 5b, 6 and 7.
    bad_tags, good_tags, answer4b = answer_question4b()
    print('\nA tagged-by-your-model version of a sentence:')
    print(bad_tags)
    print('The tagged version of this sentence from the corpus:')
    print(good_tags)
    print('\nDiscussion of the difference:')
    print(answer4b)
    answer5b = answer_question5b()
    print("\nFor Q5b:")
    print(answer5b)
    answer6 = answer_question6()
    print('\nFor Q6:')
    print(answer6)
    answer7 = answer_question7()
    print('\nFor Q7:')
    print(answer7)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--answers':
        import adrive2
        from autodrive_embed import run, carefulBind

        with open("userErrs.txt", "w") as errlog:
            run(globals(), answers, adrive2.a2answers, errlog)
    else:
        answers()
