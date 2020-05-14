#! /usr/bin/python3

import sys
import random
import string

KEY_SIZE = 16
STATE_SIZE = 16

def generateRandomInput(key_size, state_size):
    key = ""
    state = ""
    for _ in range(key_size):
        key += random.choice(string.ascii_letters)
    for _ in range(state_size):
        state += random.choice(string.ascii_letters)

    return key + " " + state

def genRandomTests(test_file_name='aes.tf', num_tests=5):

    # Open Test File
    test_file = open(test_file_name, "w")

    # Write Tests
    for _ in range(num_tests):
        test_file.write("%s\n" % \
                generateRandomInput(KEY_SIZE, STATE_SIZE))

    # Close Test File
    test_file.close()

if __name__ == '__main__':
    genRandomTests(test_file_name=sys.argv[1], num_tests=int(sys.argv[2]))
