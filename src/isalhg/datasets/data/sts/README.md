# Steiner triple system catalog (orders 3–15)

Complete listings of the pairwise non-isomorphic Steiner triple systems of
order `n ∈ {3, 7, 9, 13, 15}`, vendored verbatim from Olli Pottonen's STS
pages (retrieved 2026-07-18):

- Source: `https://pottonen.kapsi.fi/sts19/sts{n}.txt`
- Classification: P. Kaski & P. R. J. Östergård, *The Steiner triple systems
  of order 19*, Mathematics of Computation 73 (2004) 2075–2092 (the same
  enumeration machinery produces the small-order catalogues; the counts
  1, 1, 1, 2, 80 for n = 3, 7, 9, 13, 15 are the classical classification,
  cf. Colbourn & Rosa, *Triple Systems*, Oxford, 1999).

## Format

One system per line. A line is a concatenation of 3-letter blocks; letter
`a` is point 0, `b` is point 1, … Each line has `n(n-1)/6` blocks.

## Integrity

SHA-256 of the vendored files at retrieval:

```
edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb  sts3.txt
a6882624d4e84ee5447391acca0b7f73ba1cefa7895fbfffcc528f2c5e075d55  sts7.txt
dff09ebe993597a68fdadd0ddf18404419aaa8b0d30ff6d1613ff5735080ae4c  sts9.txt
4c83e5e6446e761a0d3602333dd16bab3c179dddfc0fa839f8ea8e51d8b25a9c  sts13.txt
dbd3d50d381b4d18ffdfc61e67af9f7c755d7d4baee3135fdcdb0e0e5a5c8122  sts15.txt
```

Verified at vendoring (2026-07-18, pynauty over the Levi reduction): every
listed system satisfies the Steiner axioms (every point-pair in exactly one
block), and the systems of each order are pairwise non-isomorphic with
exactly 1 / 1 / 1 / 2 / 80 isomorphism classes. The order-7 entry is
isomorphic to the in-repo Fano fixture and the order-9 entry to the in-repo
`sts_9` fixture.
