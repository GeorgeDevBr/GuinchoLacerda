import heapq
from collections import defaultdict

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text):
    freq = defaultdict(int)
    for char in text:
        freq[char] += 1

    heap = [HuffmanNode(char, freq) for char, freq in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
        merged = HuffmanNode(None, node1.freq + node2.freq)
        merged.left = node1
        merged.right = node2
        heapq.heappush(heap, merged)

    return heap[0]

def build_codes(node, prefix="", codebook={}):
    if node:
        if node.char is not None:
            codebook[node.char] = prefix
        build_codes(node.left, prefix + "0", codebook)
        build_codes(node.right, prefix + "1", codebook)
    return codebook

def huffman_compress(text):
    root = build_huffman_tree(text)
    codebook = build_codes(root)
    compressed = ''.join(codebook[char] for char in text)
    return compressed, codebook

def huffman_decompress(compressed, codebook):
    reverse_codebook = {v: k for k, v in codebook.items()}
    current_code = ""
    decompressed = []

    for bit in compressed:
        current_code += bit
        if current_code in reverse_codebook:
            decompressed.append(reverse_codebook[current_code])
            current_code = ""

    return ''.join(decompressed)
