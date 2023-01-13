# Script Name   : trie.py
# Author        : The_Average_Engineer
# Created       : 26th April 2021
# Description   : Prefix tree
# useful link   : https://en.wikipedia.org/wiki/Trie
# useful link   : https://towardsdatascience.com/implementing-a-trie-data-structure-in-python-in-less-than-100-lines-of-code-a877ea23c1a1


class TrieNode(object):
    """
    Trie node implementation.
    """

    def __init__(self, char, parent):
        self.char = char
        self.parent = parent
        self.children = []
        # Is it the last character of the string.`
        self.is_string_finished = False
        # How many times this character appeared in the addition process
        self.counter = 1


def add(node, string):
    """
    Adding a string in the trie structure
    """
    for char in string:
        found_in_child = False
        # Search for the character in the children of the present `node`
        for child in node.children:
            if child.char == char:
                # We found it, increase the counter by 1 to keep track that another
                # word has it as well
                child.counter += 1
                # And point the node to the child that contains this char
                node = child
                found_in_child = True
                break
        # We did not find it so add a new child
        if not found_in_child:
            new_node = TrieNode(char, node)
            node.children.append(new_node)
            # And then point node to the new child
            node = new_node
    # Everything finished. Mark it as the end of a word.
    node.is_string_finished = True


def chunk_into_clusters(node, threshold, clusters_nodes):
    """
    Chunk trie into clusters.
    threshold is maximum number of string a cluster can contain.
    clusters_nodes is the output/resulting list of nodes.
    """
    for child in node.children:
        if (child.counter < threshold) and (len(child.children) > 1):
            clusters_nodes.append(child)
        elif child.is_string_finished:
            clusters_nodes.append(child)
        else:
            chunk_into_clusters(
                child, threshold, clusters_nodes)  # recursive call


def find_end_nodes(node, end_nodes):
    """
    Find nodes which end strings (nodes having the attribute "is_string_finished" set to True).
    threshold is the maximum number of string a cluster can contain.
    clusters_nodes is the output/resulting list of nodes.
    """
    for child in node.children:
        if child.is_string_finished:
            end_nodes.append(child)
        find_end_nodes(child, end_nodes)  # recursive call


def retrieve_string(node):
    """
    retrieve string from node.
    """
    string = ""
    while node is not None:  # while node is not root
        string = node.char + string
        node = node.parent
    return string
