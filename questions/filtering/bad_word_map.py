# this needs to be configured per project based on what words are acceptable to your use case
# e.g. "torturers" would be blocked by LLMS so would need to be replaced with a kinder word
bad_word_to_good_word = {
    'torturers': 'baddies',
}

good_word_to_bad_word = {v:k for k,v in bad_word_to_good_word.items()}
