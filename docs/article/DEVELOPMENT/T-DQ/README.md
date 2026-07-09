# Scope T-DQ — data questions that gate corpus scale

Open empirical questions from `DATA.md` whose answer is a single measurement, and
whose answer decides the size of a corpus rather than the design of a method. The
live one is DQ3': the applications became HGED-free, so `w*` wall-clock is now the
*only* gate on how large the MDS / clustering / kNN corpora can be. One timing run
on a real HIC instance decides whether the paper carries a real-world anchor or
stays on synthetic planted families plus small combinatorial designs. The
measurement must be taken on the canonical encoder `w*_c`, not on the greedy
default it replaces, or it times the wrong algorithm.
